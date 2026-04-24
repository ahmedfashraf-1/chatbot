memory = {}

MAX_HISTORY = 6

def get_history(user_id):
    return memory.get(user_id, [])

def save(user_id, role, content):
    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({
        "role": role,
        "content": content
    })

    # trim
    memory[user_id] = memory[user_id][-MAX_HISTORY:]