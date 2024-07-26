from pymongo import ReturnDocument
from Grabber import collection, user_collection

async def ac(user_id: int, character_id: int):
    try:
        character = await collection.find_one({'id': character_id})
        if not character:
            return f"Character with ID {character_id} not found."

        result = await user_collection.find_one_and_update(
            {'id': user_id},
            {'$push': {'characters': character}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        if result:
            return f"Character with ID {character_id} added to user {user_id}."
        else:
            return f"Failed to add character with ID {character_id} to user {user_id}."
    except Exception as e:
        print(f"Error in add_character: {e}")
        return "An error occurred while adding the character."

async def rc(user_id: int, character_id: int):
    try:
        result = await user_collection.find_one_and_update(
            {'id': user_id, 'characters.id': character_id},
            {'$pull': {'characters': {'id': character_id}}},
            return_document=ReturnDocument.AFTER
        )
        if result:
            return f"One instance of character with ID {character_id} removed from user {user_id}."
        else:
            return f"Character with ID {character_id} not found for user {user_id}."
    except Exception as e:
        print(f"Error in remove_character: {e}")
        return "An error occurred while removing the character."