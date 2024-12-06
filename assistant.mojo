from python import Python
from python.object import PythonObject

struct DBParams:
    var dbname: PythonObject
    var user: PythonObject
    var password: PythonObject
    var host: PythonObject
    var port: PythonObject

    fn __init__(inout self) raises:
        # Initialize with Python string objects
        var builtins = Python.import_module("builtins")
        self.dbname = builtins.str("memory_agent")
        self.user = builtins.str("llama")
        self.password = builtins.str("llama")
        self.host = builtins.str("localhost")
        self.port = builtins.str("5432")

fn debug_print(msg: String):
    print("DEBUG:", msg)

fn create_conversation_dict(system_prompt: PythonObject, user_prompt: PythonObject) raises -> PythonObject:
    var builtins = Python.import_module("builtins")
    var system_dict = builtins.dict()
    var user_dict = builtins.dict()
    
    system_dict.__setitem__("role", builtins.str("system"))
    system_dict.__setitem__("content", system_prompt)
    user_dict.__setitem__("role", builtins.str("user"))
    user_dict.__setitem__("content", user_prompt)
    
    var messages = builtins.list()
    messages.append(system_dict)
    messages.append(user_dict)
    return messages

fn connect_db(params: DBParams) raises -> PythonObject:
    var psycopg = Python.import_module("psycopg")
    return psycopg.connect(
        dbname=params.dbname,
        user=params.user,
        password=params.password,
        host=params.host,
        port=params.port
    )

fn get_python_input() raises -> PythonObject:
    var builtins = Python.import_module("builtins")
    return builtins.input()

fn main() raises:
    debug_print("Starting Memory Agent")
    
    # Import required modules
    var psycopg = Python.import_module("psycopg")
    var chromadb = Python.import_module("chromadb")
    var ollama = Python.import_module("ollama")
    var builtins = Python.import_module("builtins")
    
    # Initialize database parameters
    var params = DBParams()
    
    # Initialize system prompt
    var system_prompt = builtins.str("""
    You are an AI assistant that has memory of every conversation you have ever had with this user.
    On every prompt from the user, the system has checked for any relevant messages you have had with the user.
    If any embedded previous conversations are attached, use them for context to responding to the user.
    """)
    
    debug_print("Testing database connection...")
    try:
        var conn = connect_db(params)
        conn.close()
        debug_print("Database connection successful")
    except:
        debug_print("Database connection failed")
        return
    
    debug_print("Testing ChromaDB...")
    try:
        var client = chromadb.Client()
        debug_print("ChromaDB client created successfully")
    except:
        debug_print("ChromaDB client creation failed")
        return
    
    debug_print("Basic initialization complete")
    print("\nMemory Agent Ready")
    print("Type 'quit' to exit")
    
    # Simple chat loop for testing
    while True:
        print("\nUSER: ")
        var user_input = get_python_input()
        
        if str(user_input) == "quit":
            break
            
        # Test conversation dict creation
        var messages = create_conversation_dict(system_prompt, user_input)
        
        # Basic Ollama test
        var response = ollama.chat(
            model="qwq",
            messages=messages
        )
        
        print("\nASSISTANT:")
        print(str(response.__getitem__("message").__getitem__("content")))
