from .vectorstore import vector_db

def retrive_chunk(user_id, conversation_id, query, k=5):
    result = vector_db.similarity_search(
        query=query,
        k=k,
        filter={
            "$and" : [
                {"conversation_id" : conversation_id},
                {"user_id" : user_id}
            ]
        }
    )
    
    return result
    

def retrieve_chunk_with_score(user_id, conversation_id, query):
    result = vector_db.similarity_search_with_score(
        query=query,
        k=3,
        filter={
            "$and" :[
                {"conversation_id" : conversation_id},
                {"user_id" : user_id}
            ]
        }
    )
    
    return result