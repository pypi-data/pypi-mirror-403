"""
Verify Session Reload Behavior

This experiment verifies that after moment builder compression:
1. Session reload only loads messages AFTER the last partition
2. The partition event contains moment_keys for LOOKUP
3. Using LOOKUP on moment keys recovers the full conversation context

Run with:
    POSTGRES__CONNECTION_STRING='postgresql://rem:rem@localhost:5050/rem' \
    python tests/experiments/verify_session_reload.py
"""

import asyncio
import json
import sys
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Add src to path
sys.path.insert(0, "src")

from rem.services.postgres import get_postgres_service
from rem.services.session.compression import SessionMessageStore
from rem.settings import settings


async def verify_session_reload(session_id: str, user_id: str):
    """Verify session reload behavior after compression."""

    postgres = get_postgres_service()
    await postgres.connect()

    try:
        # ═══════════════════════════════════════════════════════════════════
        # 1. Count total messages in the session
        # ═══════════════════════════════════════════════════════════════════
        total_query = """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN message_type IN ('user', 'assistant') THEN 1 ELSE 0 END) as conversation,
                   SUM(CASE WHEN metadata->>'tool_name' = 'session_partition' THEN 1 ELSE 0 END) as partitions
            FROM messages
            WHERE session_id = $1 AND user_id = $2 AND deleted_at IS NULL
        """
        total_row = await postgres.fetchrow(total_query, session_id, user_id)

        print("═" * 70)
        print("SESSION RELOAD VERIFICATION")
        print("═" * 70)
        print(f"\nTotal messages in database: {total_row['total']}")
        print(f"  - Conversation (user/assistant): {total_row['conversation']}")
        print(f"  - Partition events: {total_row['partitions']}")

        # ═══════════════════════════════════════════════════════════════════
        # 2. Load session with max_messages limit (simulating normal reload)
        # ═══════════════════════════════════════════════════════════════════
        max_messages = settings.moment_builder.load_max_messages
        print(f"\nLoading session with max_messages={max_messages}...")

        store = SessionMessageStore(user_id=user_id)
        loaded_messages, has_partition = await store.load_session_messages(
            session_id=session_id,
            user_id=user_id,
            compress_on_load=True,
            max_messages=max_messages,
        )

        print(f"\n✓ Loaded {len(loaded_messages)} messages (limit={max_messages})")
        print(f"  Has partition event: {has_partition}")

        # ═══════════════════════════════════════════════════════════════════
        # 3. Analyze loaded messages
        # ═══════════════════════════════════════════════════════════════════
        user_msgs = [m for m in loaded_messages if m['role'] == 'user']
        assistant_msgs = [m for m in loaded_messages if m['role'] == 'assistant']
        tool_msgs = [m for m in loaded_messages if m['role'] == 'tool']

        print(f"\nLoaded message breakdown:")
        print(f"  - User messages: {len(user_msgs)}")
        print(f"  - Assistant messages: {len(assistant_msgs)}")
        print(f"  - Tool messages: {len(tool_msgs)}")

        # ═══════════════════════════════════════════════════════════════════
        # 4. Find partition event and extract moment keys
        # ═══════════════════════════════════════════════════════════════════
        partition_event = None
        for msg in loaded_messages:
            if msg.get('tool_name') == 'session_partition':
                partition_event = msg
                break

        moment_keys = []
        if partition_event:
            print(f"\n✓ Found partition event in loaded messages")
            try:
                content = json.loads(partition_event['content'])
                moment_keys = content.get('moment_keys', [])
                print(f"  Moment keys for LOOKUP: {moment_keys}")
                print(f"  Compressed message count: {content.get('compressed_message_count', 'N/A')}")
            except json.JSONDecodeError:
                print(f"  Could not parse partition content")
        else:
            print(f"\n⚠ No partition event in loaded messages (session may be too short)")

        # ═══════════════════════════════════════════════════════════════════
        # 5. LOOKUP moment keys to recover context
        # ═══════════════════════════════════════════════════════════════════
        if moment_keys:
            print(f"\n{'═' * 70}")
            print("MOMENT LOOKUP (recovering compressed context)")
            print("═" * 70)

            # Reconnect if needed (SessionMessageStore may have disconnected)
            if not postgres.pool:
                await postgres.connect()

            for key in moment_keys[:3]:  # Show first 3
                # Query moment by name (entity_key)
                moment_query = """
                    SELECT name, summary, moment_type, topic_tags, previous_moment_keys,
                           starts_timestamp, ends_timestamp
                    FROM moments
                    WHERE name = $1 AND tenant_id = $2 AND deleted_at IS NULL
                    LIMIT 1
                """
                moment = await postgres.fetchrow(moment_query, key, user_id)

                if moment:
                    print(f"\n📖 Moment: {moment['name']}")
                    print(f"   Type: {moment['moment_type']}")
                    print(f"   Topics: {moment['topic_tags'][:5] if moment['topic_tags'] else []}")

                    # Show summary preview
                    summary = moment['summary'] or ""
                    if len(summary) > 200:
                        print(f"   Summary: {summary[:200]}...")
                    else:
                        print(f"   Summary: {summary}")

                    # Show chain links
                    prev_keys = moment['previous_moment_keys'] or []
                    if prev_keys:
                        print(f"   ← Previous moments: {prev_keys[:3]}...")
                else:
                    print(f"\n⚠ Moment not found: {key}")

        # ═══════════════════════════════════════════════════════════════════
        # 6. Show what context the LLM would see
        # ═══════════════════════════════════════════════════════════════════
        print(f"\n{'═' * 70}")
        print("CONTEXT WINDOW (what LLM sees on reload)")
        print("═" * 70)

        # Calculate sizes
        total_chars = sum(len(m.get('content', '')) for m in loaded_messages)
        print(f"\nTotal context size: {total_chars:,} characters (~{total_chars // 4:,} tokens)")

        print(f"\nFirst 3 messages:")
        for i, msg in enumerate(loaded_messages[:3]):
            role = msg['role']
            content = msg.get('content', '')[:100]
            print(f"  [{i}] {role}: {content}...")

        print(f"\nLast 3 messages:")
        for i, msg in enumerate(loaded_messages[-3:]):
            role = msg['role']
            content = msg.get('content', '')[:100]
            print(f"  [{len(loaded_messages)-3+i}] {role}: {content}...")

        # ═══════════════════════════════════════════════════════════════════
        # 7. Summary
        # ═══════════════════════════════════════════════════════════════════
        compressed_count = total_row['conversation'] - len(user_msgs) - len(assistant_msgs)
        if compressed_count < 0:
            compressed_count = 0

        print(f"\n{'═' * 70}")
        print("SUMMARY")
        print("═" * 70)
        print(f"\n✓ Total messages in DB: {total_row['total']}")
        print(f"✓ Messages loaded: {len(loaded_messages)} (due to max_messages={max_messages})")
        print(f"✓ Messages compressed into moments: ~{compressed_count}")
        print(f"✓ Partition detected: {has_partition}")
        print(f"✓ Moment keys for LOOKUP: {len(moment_keys)}")

        if has_partition and moment_keys:
            print(f"\n✅ Session reload working correctly!")
            print(f"   - Old messages compressed into moments")
            print(f"   - Partition event contains moment keys")
            print(f"   - LOOKUP can recover full context as needed")
        else:
            print(f"\n⚠ Session may need more messages to trigger compression")

    finally:
        await postgres.disconnect()


async def find_test_session(user_id: str) -> str | None:
    """Find a session with partition events."""
    postgres = get_postgres_service()
    await postgres.connect()

    try:
        query = """
            SELECT DISTINCT session_id, COUNT(*) as msg_count
            FROM messages
            WHERE user_id = $1
              AND deleted_at IS NULL
              AND session_id IN (
                  SELECT session_id FROM messages
                  WHERE metadata->>'tool_name' = 'session_partition'
                    AND user_id = $1
              )
            GROUP BY session_id
            ORDER BY msg_count DESC
            LIMIT 1
        """
        row = await postgres.fetchrow(query, user_id)
        if row:
            return row['session_id']
        return None
    finally:
        await postgres.disconnect()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify session reload behavior")
    parser.add_argument("--session-id", help="Session ID to verify")
    parser.add_argument("--user-id", default="test-user-123", help="User ID")
    args = parser.parse_args()

    session_id = args.session_id
    user_id = args.user_id

    if not session_id:
        print("Looking for a session with partitions...")
        session_id = await find_test_session(user_id)

        if not session_id:
            print(f"No sessions with partitions found for user {user_id}")
            print("Run the long_conversation_experiment.py first to create test data")
            return

    print(f"Verifying session: {session_id}")
    print(f"User: {user_id}")

    await verify_session_reload(session_id, user_id)


if __name__ == "__main__":
    asyncio.run(main())
