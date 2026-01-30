from typing import TypedDict



class Person(TypedDict):
    name: str
    age: int





def say_hello():
    print("Hello, World!!!")





def return_a_string() -> str:
    return "a"




def return_a_person() -> Person:
    return {
        "name": "John",
        "age": 30
    }


#lolol