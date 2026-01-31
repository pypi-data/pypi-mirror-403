"""
Long Conversation Experiment - Full Cycle

This experiment:
1. Creates a long conversation with ~80 messages across 10 topics
2. Runs moment builder multiple times to create partitions
3. Verifies session reload loads only recent messages
4. Demonstrates moment chaining via previous_moment_keys

Run with:
    POSTGRES__CONNECTION_STRING='postgresql://rem:rem@localhost:5050/rem' \
    python tests/experiments/long_conversation_experiment.py
"""

import asyncio
import json
import sys
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Add src to path
sys.path.insert(0, "src")

from rem.services.postgres import get_postgres_service
from rem.services.postgres.repository import Repository
from rem.models.entities import Message, Moment
from rem.agentic.agents.moment_builder import MomentBuilder
from rem.services.session.compression import SessionMessageStore
from rem.settings import settings


# Test topics with realistic conversation patterns
TOPICS = [
    ("project_planning", [
        ("user", "I'm thinking about starting a new mobile app project"),
        ("assistant", "That's exciting! What kind of app are you thinking about? Mobile development offers many possibilities - from native iOS/Android to cross-platform solutions like React Native or Flutter."),
        ("user", "A fitness tracking app that connects with wearables"),
        ("assistant", "Great choice! Fitness apps have strong market demand. For wearable integration, you'll want to consider HealthKit for iOS and Google Fit for Android. What wearables are you targeting?"),
        ("user", "Mainly Garmin and Apple Watch"),
        ("assistant", "Both have solid APIs. Garmin Connect IQ SDK and WatchKit for Apple Watch. You'll need to handle data sync, offline storage, and potentially background processing. Should we outline the technical architecture?"),
        ("user", "Yes, let's do that"),
        ("assistant", "I'd suggest: 1) React Native for cross-platform UI, 2) Node.js backend with PostgreSQL, 3) Redis for real-time sync, 4) S3 for media storage. The wearable SDKs would be native modules. Does this align with your team's skills?"),
    ]),
    ("debugging_session", [
        ("user", "I'm getting a weird null pointer exception in my code"),
        ("assistant", "Null pointer exceptions are common but can be tricky. Can you share the stack trace? That will help identify exactly where the null reference is occurring."),
        ("user", "It's in the UserService class, line 45, when calling user.getEmail()"),
        ("assistant", "So the `user` object is null when you're trying to access getEmail(). This typically happens when: 1) The database query returned null, 2) The user ID doesn't exist, or 3) There's a race condition. What does the code look like before line 45?"),
        ("user", "User user = userRepository.findById(userId);"),
        ("assistant", "There's your issue - findById can return null if the user doesn't exist. You should either use Optional<User> and handle the empty case, or add a null check. Would you like me to show both approaches?"),
        ("user", "Show me the Optional approach"),
        ("assistant", "Here's the pattern: `userRepository.findById(userId).orElseThrow(() -> new UserNotFoundException(userId))`. This makes the absence explicit and gives you a meaningful exception instead of NPE."),
    ]),
    ("code_review", [
        ("user", "Can you review this function I wrote for calculating compound interest?"),
        ("assistant", "I'd be happy to review it! Please share the code and I'll look at correctness, performance, readability, and edge cases."),
        ("user", "def compound_interest(principal, rate, time, n=12): return principal * (1 + rate/n) ** (n*time)"),
        ("assistant", "The formula is correct for compound interest! A few suggestions: 1) Add type hints, 2) Validate inputs (rate > 0, time >= 0, n > 0), 3) Consider using Decimal for financial precision, 4) Add a docstring. Should I show the improved version?"),
        ("user", "Yes please, especially the Decimal part"),
        ("assistant", "```python\nfrom decimal import Decimal, ROUND_HALF_UP\n\ndef compound_interest(principal: Decimal, rate: Decimal, years: int, compounds_per_year: int = 12) -> Decimal:\n    \"\"\"Calculate compound interest with financial precision.\"\"\"\n    if rate <= 0 or years < 0 or compounds_per_year <= 0:\n        raise ValueError(\"Invalid input parameters\")\n    result = principal * (1 + rate/compounds_per_year) ** (compounds_per_year * years)\n    return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)\n```"),
        ("user", "That's much better, thank you"),
        ("assistant", "You're welcome! The Decimal type ensures you don't get floating-point errors that could add up in financial calculations. Also note I renamed the parameters to be more descriptive."),
    ]),
    ("architecture_discussion", [
        ("user", "Should we use microservices or a monolith for our new e-commerce platform?"),
        ("assistant", "Great question - it depends on several factors. What's your team size, expected traffic, and deployment timeline? Microservices offer scalability but add operational complexity."),
        ("user", "Team of 5, expecting 10k users initially, need to launch in 3 months"),
        ("assistant", "For a team of 5 with a 3-month timeline, I'd recommend starting with a well-structured monolith. You can always extract services later. Microservices would slow you down initially and create operational overhead your small team may struggle to handle."),
        ("user", "That makes sense. What about the database design?"),
        ("assistant", "For e-commerce, PostgreSQL is solid. Key tables: users, products, orders, order_items, inventory, payments. Use proper indexing on frequently queried columns. Consider read replicas if read traffic grows. Should we sketch out the schema?"),
        ("user", "Yes, especially the orders and inventory relationship"),
        ("assistant", "Orders table: id, user_id, status, total, created_at. Order_items: id, order_id, product_id, quantity, price_at_time. Inventory: product_id, quantity, reserved_quantity. The reserved_quantity handles items in carts not yet purchased. Use transactions when updating inventory during checkout."),
    ]),
    ("learning_python", [
        ("user", "I want to learn about Python decorators"),
        ("assistant", "Decorators are a powerful Python feature! They're essentially functions that modify other functions. The @syntax is just syntactic sugar. Would you like to start with a simple example?"),
        ("user", "Yes, something simple please"),
        ("assistant", "Here's a basic timer decorator:\n```python\nimport time\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} took {time.time()-start:.2f}s')\n        return result\n    return wrapper\n```\nUse it with @timer above any function."),
        ("user", "How do I pass arguments to the decorator itself?"),
        ("assistant", "You need a decorator factory - a function that returns a decorator:\n```python\ndef repeat(n):\n    def decorator(func):\n        def wrapper(*args, **kwargs):\n            for _ in range(n):\n                result = func(*args, **kwargs)\n            return result\n        return wrapper\n    return decorator\n\n@repeat(3)\ndef greet(): print('hello')\n```"),
        ("user", "I think I get it now"),
        ("assistant", "Great! The key insight is: decorators without args are functions, decorators with args are functions that return decorators. Also check out functools.wraps to preserve the original function's metadata."),
    ]),
    ("database_optimization", [
        ("user", "Our database queries are getting slow as data grows"),
        ("assistant", "Performance degradation with data growth is common. Let's diagnose: 1) Are you using EXPLAIN ANALYZE? 2) What's your current indexing strategy? 3) Are there any N+1 query patterns?"),
        ("user", "I think we have N+1 issues in our ORM queries"),
        ("assistant", "N+1 is a classic ORM problem. If you're using SQLAlchemy, use `joinedload` or `selectinload` for eager loading. For Django, use `select_related` (foreign keys) and `prefetch_related` (many-to-many). Which ORM are you using?"),
        ("user", "Django ORM"),
        ("assistant", "Perfect. Change `User.objects.all()` to `User.objects.select_related('profile').prefetch_related('orders')` when you need related data. Also install django-debug-toolbar to see query counts per request. That's often eye-opening!"),
        ("user", "What about read replicas?"),
        ("assistant", "Good for read-heavy workloads. Django supports multiple databases via DATABASE_ROUTERS. Route reads to replica, writes to primary. Be aware of replication lag - if you write then immediately read, use the primary. Most cloud providers handle replica setup automatically."),
    ]),
    ("api_design", [
        ("user", "What's the best practice for API versioning?"),
        ("assistant", "There are three main approaches: 1) URL path (/v1/users), 2) Header (Accept: application/vnd.api.v1+json), 3) Query param (?version=1). URL path is most common and explicit. What's your use case?"),
        ("user", "We have mobile apps that can't update as fast as our API"),
        ("assistant", "Then URL versioning (/v1/, /v2/) is ideal. It's explicit, cacheable, and easy to route. Keep old versions running while deprecating them. Set a deprecation policy (e.g., support last 2 versions). Monitor which versions are still in use."),
        ("user", "How do we handle breaking changes?"),
        ("assistant", "For breaking changes: 1) Bump major version, 2) Communicate early (deprecation headers, docs, emails), 3) Provide migration guides, 4) Set sunset date. Non-breaking changes (additive) can go in same version. Never remove fields without versioning."),
        ("user", "Should we use GraphQL instead?"),
        ("assistant", "GraphQL solves versioning differently - clients request exactly what they need, so you can add fields without breaking anyone. However, it adds complexity (resolvers, N+1, caching). REST with good versioning is often simpler for mobile. Consider your team's GraphQL experience."),
    ]),
    ("testing_strategies", [
        ("user", "How should I structure my test suite?"),
        ("assistant", "The testing pyramid is a good starting point: lots of unit tests (fast, isolated), some integration tests (test interactions), few E2E tests (slow, brittle). What's your current testing situation?"),
        ("user", "We have some unit tests but no integration tests"),
        ("assistant", "Integration tests are crucial for catching issues unit tests miss. Start with: 1) API endpoint tests, 2) Database interaction tests, 3) External service mocking. Use pytest fixtures for setup. Want to see a pattern for API testing?"),
        ("user", "Yes, for a FastAPI application"),
        ("assistant", "```python\nimport pytest\nfrom httpx import AsyncClient\n\n@pytest.fixture\nasync def client():\n    async with AsyncClient(app=app, base_url='http://test') as ac:\n        yield ac\n\nasync def test_create_user(client):\n    response = await client.post('/users', json={'name': 'test'})\n    assert response.status_code == 201\n```\nThis tests the full request/response cycle."),
        ("user", "What about mocking external APIs?"),
        ("assistant", "Use respx for httpx or responses for requests. Example: `@respx.mock def test_payment(): respx.post('https://stripe.com/...').respond(json={'id': 'ch_123'})`. This prevents real API calls in tests and lets you test error scenarios."),
    ]),
    ("deployment_pipeline", [
        ("user", "We're setting up CI/CD for the first time"),
        ("assistant", "Exciting! A good CI/CD pipeline: 1) Lint/format check, 2) Run tests, 3) Build artifacts, 4) Deploy to staging, 5) Run E2E tests, 6) Deploy to prod. Are you using GitHub Actions, GitLab CI, or something else?"),
        ("user", "GitHub Actions"),
        ("assistant", "Great choice. Start with a workflow that runs on PR: lint, test, build. Then add a deploy workflow on merge to main. Use environment protection rules for production deploys. Want me to show a basic workflow structure?"),
        ("user", "Yes, especially the environment protection part"),
        ("assistant", "In your repo settings, create 'staging' and 'production' environments. Add protection rules to production: require approval, restrict to main branch. In workflow:\n```yaml\njobs:\n  deploy-prod:\n    environment: production\n    steps: ...\n```\nNow prod deploys need approval."),
        ("user", "How do we handle secrets?"),
        ("assistant", "GitHub Actions secrets are secure and scoped. Add them in repo settings. Reference as `${{ secrets.MY_SECRET }}`. For production, use environment-level secrets so they're only available in that environment. Never log secrets or put them in artifacts."),
    ]),
    ("security_review", [
        ("user", "Can you review our authentication implementation?"),
        ("assistant", "Happy to help with security! What authentication method are you using - sessions, JWT, OAuth? And how are you storing credentials?"),
        ("user", "JWT with bcrypt for password hashing"),
        ("assistant", "Good foundation! Key things to verify: 1) JWT expiry is short (15-60 min), 2) Refresh tokens are single-use and stored securely, 3) bcrypt cost factor is >= 12, 4) Tokens are in httpOnly cookies (not localStorage). Any of these concerning?"),
        ("user", "We're storing JWTs in localStorage"),
        ("assistant", "That's a security risk - localStorage is accessible to any JavaScript on the page, making you vulnerable to XSS. Move JWTs to httpOnly cookies with SameSite=Strict. This prevents both XSS token theft and CSRF attacks."),
        ("user", "What about the refresh token flow?"),
        ("assistant", "Refresh tokens should: 1) Be stored in DB (not just signed), 2) Be single-use (delete after rotation), 3) Have longer expiry but still limited (e.g., 7 days), 4) Support revocation on logout. The rotation prevents token theft from being permanent."),
    ]),
]


async def create_test_messages(session_id: str, user_id: str, topic_count: int = 10):
    """Create test messages for the long conversation experiment."""

    postgres = get_postgres_service()
    await postgres.connect()

    try:
        repo = Repository(Message, "messages", db=postgres)
        # Use naive datetime (CoreModel strips timezone)
        base_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=5)
        message_index = 0

        print(f"\nCreating messages for {topic_count} topics...")

        for topic_idx, (topic_name, exchanges) in enumerate(TOPICS[:topic_count]):
            print(f"  Topic {topic_idx + 1}: {topic_name} ({len(exchanges)} messages)")

            for exchange_idx, (role, content) in enumerate(exchanges):
                msg_time = base_time + timedelta(minutes=message_index * 2)

                msg = Message(
                    id=uuid4(),
                    tenant_id=user_id,
                    user_id=user_id,
                    session_id=session_id,
                    message_type=role,
                    content=content,
                    metadata={"topic": topic_name, "message_index": message_index},
                    created_at=msg_time,
                )
                await repo.upsert(msg, generate_embeddings=False)
                message_index += 1

        print(f"\n✓ Created {message_index} messages")
        return message_index

    finally:
        await postgres.disconnect()


async def run_moment_builder_cycles(session_id: str, user_id: str, cycles: int = 5):
    """Run moment builder multiple times to create partitions."""

    print(f"\nRunning {cycles} moment builder cycles...")

    for cycle in range(cycles):
        builder = MomentBuilder(
            session_id=session_id,
            user_id=user_id,
            force=True,  # Force compression regardless of lag
        )

        result = await builder.run()

        if result and result.moments_created > 0:
            print(f"  Cycle {cycle + 1}: Created {result.moments_created} moment(s)")
        else:
            print(f"  Cycle {cycle + 1}: No new moments (all messages compressed)")

        # Small delay between cycles
        await asyncio.sleep(0.1)

    print(f"\n✓ Completed {cycles} compression cycles")


async def verify_results(session_id: str, user_id: str):
    """Verify the compression and reload behavior."""

    postgres = get_postgres_service()
    await postgres.connect()

    try:
        print("\n" + "═" * 70)
        print("VERIFICATION RESULTS")
        print("═" * 70)

        # Count total messages
        msg_query = """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN message_type IN ('user', 'assistant') THEN 1 ELSE 0 END) as conversation,
                   SUM(CASE WHEN metadata->>'tool_name' = 'session_partition' THEN 1 ELSE 0 END) as partitions
            FROM messages
            WHERE session_id = $1 AND user_id = $2 AND deleted_at IS NULL
        """
        msg_row = await postgres.fetchrow(msg_query, session_id, user_id)

        print(f"\nMessages in database:")
        print(f"  Total: {msg_row['total']}")
        print(f"  Conversation (user/assistant): {msg_row['conversation']}")
        print(f"  Partition events: {msg_row['partitions']}")

        # Count moments
        moment_query = """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN array_length(previous_moment_keys, 1) > 0 THEN 1 END) as with_links
            FROM moments
            WHERE tenant_id = $1 AND deleted_at IS NULL
        """
        moment_row = await postgres.fetchrow(moment_query, user_id)

        print(f"\nMoments created:")
        print(f"  Total: {moment_row['total']}")
        print(f"  With backward links: {moment_row['with_links']}")

        # Verify moment chaining
        chain_query = """
            SELECT name, previous_moment_keys
            FROM moments
            WHERE tenant_id = $1 AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT 3
        """
        chain_rows = await postgres.fetch(chain_query, user_id)

        if chain_rows:
            print(f"\nMoment Chain (most recent 3):")
            for row in chain_rows:
                keys = row['previous_moment_keys'] or []
                print(f"  {row['name'][:40]}... → {len(keys)} links")

        # Simulate session reload
        print(f"\n{'─' * 70}")
        print("SESSION RELOAD SIMULATION")
        print("─" * 70)

        max_messages = settings.moment_builder.load_max_messages
        store = SessionMessageStore(user_id=user_id)
        loaded_messages, has_partition = await store.load_session_messages(
            session_id=session_id,
            user_id=user_id,
            compress_on_load=True,
            max_messages=max_messages,
        )

        loaded_user = len([m for m in loaded_messages if m['role'] == 'user'])
        loaded_assistant = len([m for m in loaded_messages if m['role'] == 'assistant'])
        loaded_tool = len([m for m in loaded_messages if m['role'] == 'tool'])

        print(f"\nWith max_messages={max_messages}:")
        print(f"  Loaded messages: {len(loaded_messages)}")
        print(f"    - User: {loaded_user}")
        print(f"    - Assistant: {loaded_assistant}")
        print(f"    - Tool: {loaded_tool}")
        print(f"  Has partition event: {has_partition}")

        # Calculate compression ratio
        total_conv = msg_row['conversation']
        loaded_conv = loaded_user + loaded_assistant
        compressed_count = total_conv - loaded_conv
        if compressed_count < 0:
            compressed_count = 0

        print(f"\n{'─' * 70}")
        print("SUMMARY")
        print("─" * 70)
        print(f"\n✓ Messages BEFORE partition (compressed into moments): {compressed_count}")
        print(f"✓ Messages AFTER partition (loaded in full):           {loaded_conv}")
        print(f"✓ Compression ratio: {total_conv}:{loaded_conv} ({(1 - loaded_conv/max(total_conv,1))*100:.1f}% reduction)")

        if has_partition and moment_row['total'] > 0:
            print(f"\n✅ Long conversation experiment successful!")
            print(f"   - {msg_row['partitions']} partitions created")
            print(f"   - {moment_row['total']} moments with chaining")
            print(f"   - Session reload efficiently loads only recent context")
        else:
            print(f"\n⚠ Experiment may need more data or compression cycles")

    finally:
        await postgres.disconnect()


async def cleanup_test_data(session_id: str, user_id: str):
    """Clean up test data from previous runs."""

    postgres = get_postgres_service()
    await postgres.connect()

    try:
        # Delete messages for this session
        await postgres.execute(
            "DELETE FROM messages WHERE session_id = $1 AND user_id = $2",
            (session_id, user_id)
        )

        # Delete moments for this user
        await postgres.execute(
            "DELETE FROM moments WHERE tenant_id = $1",
            (user_id,)
        )

        print("✓ Cleaned up previous test data")

    finally:
        await postgres.disconnect()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Long conversation experiment")
    parser.add_argument("--topics", type=int, default=10, help="Number of topics")
    parser.add_argument("--cycles", type=int, default=5, help="Compression cycles")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip cleanup")
    args = parser.parse_args()

    session_id = str(uuid4())
    user_id = "test-user-123"

    print("═" * 70)
    print("LONG CONVERSATION EXPERIMENT")
    print("═" * 70)
    print(f"\nSession: {session_id}")
    print(f"User: {user_id}")
    print(f"Topics: {args.topics}")
    print(f"Compression cycles: {args.cycles}")

    if not args.no_cleanup:
        await cleanup_test_data(session_id, user_id)

    # Create test messages
    await create_test_messages(session_id, user_id, args.topics)

    # Run compression cycles
    await run_moment_builder_cycles(session_id, user_id, args.cycles)

    # Verify results
    await verify_results(session_id, user_id)

    print(f"\n✓ Experiment complete")
    print(f"  Session ID: {session_id}")


if __name__ == "__main__":
    asyncio.run(main())
