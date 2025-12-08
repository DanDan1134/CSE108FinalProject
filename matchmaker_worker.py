import os
import time
import redis
import json
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

QUEUE_KEY = "matchmaking_queue"
EVENT_CHANNEL = "events"
START_GAME_CHANNEL = "start_game"

def start_matchmaker():
    """
    Main matchmaking loop.
    
    Blocks waiting for players in queue, pairs them, creates games,
    and publishes match_found events.
    """
    print("Matchmaker worker started")
    print(f"Watching queue: {QUEUE_KEY}")
    print(f"Publishing to: {EVENT_CHANNEL}, {START_GAME_CHANNEL}")
    
    while True:
        try:
            # Block until at least one player is available
            """result = r.brpop(QUEUE_KEY, timeout=0)
            if not result:
                continue
            
            _, p1 = result"""

            result = r.brpop(QUEUE_KEY, timeout=0)
            print("BRPOP raw result:", result, type(result))

            if result is None:
                print("BRPOP returned None, skipping iteration")
                continue

            # Verify it’s a list/tuple
            if not isinstance(result, (list, tuple)) or len(result) != 2:
                print("Unexpected BRPOP format, skipping iteration")
                continue

            _, p1 = result
            print("P1:", p1)
            
            # Try to get second player immediately
            p2 = r.rpop(QUEUE_KEY)
            
            if not p2:
                # Only one player available, push back and wait
                r.lpush(QUEUE_KEY, p1)
                time.sleep(1)
                continue
            
            # Ensure we don't match a player with themselves
            if p1 == p2:
                r.lpush(QUEUE_KEY, p1)
                continue
            
            # Import here to avoid circular dependencies
            from game import create_game
            
            # Create game in Redis
            room = create_game(r, p1, p2)
            
            print(f"Matched: Player {p1} vs Player {p2} in room {room}")
            
            # Notify web server via pubsub that match was found
            match_found_payload = {
                "type": "match_found",
                "room": room,
                "players": [p1, p2]
            }
            r.publish(EVENT_CHANNEL, json.dumps(match_found_payload))
            
            # Signal game_worker to start timer for this room
            start_game_payload = {
                "room": room,
                "players": [p1, p2]
            }
            r.publish(START_GAME_CHANNEL, json.dumps(start_game_payload))
            
        except redis.RedisError as e:
            print(f"Redis error in matchmaker: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"Unexpected error in matchmaker: {e}")
            time.sleep(1)

if __name__ == "__main__":
    print("=" * 60)
    print("WORDLE BATTLE - MATCHMAKER WORKER")
    print("=" * 60)
    start_matchmaker()