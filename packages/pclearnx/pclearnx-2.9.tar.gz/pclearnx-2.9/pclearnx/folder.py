import os
import shutil
from pathlib import Path

def build(folder_name):
    # Create the destination folder if it doesn't exist
    folder_path = Path(folder_name)

    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)
        print("Done")
    else:
        print(f"Folder '{folder_name}' already exists.")

    # Path to the current package directory (where this file is located)
    current_dir = Path(__file__).parent

    # List of files you want to copy from the package
    files_to_copy = [ 
    
        "BinarySearch.java",
        "LinearSearch.java",
        "BubbleSort.java",
        "InsertionSort.java",
        "SelectionSort.java",
        "ShellSort.java",
        "HashingLinearProbing.java",
        "hashing.java",
        "StackArray.java",
        "QueueArray.java",
        "CircularQueue.java",
        "InxToPostxWithoutImport.java",
        "Postfix.java",
        "parenthesis.java",
        "SinglyLinkedList.java",
        "CircularLinkedList.java",
        "DoublyLinkedList.java",
        "PolynomialAddition.java",
        "StackLinkedList.java",
        "Linked_Queue.java",
        "Priority_Queue.java",
        "DoubleEndedQueueLinkedList.java",
        "BST.java",
        "MaxHeap.java",
        "MinHeap.java",
        "HeapOperations.java",
        "AdjacencyMatrix.java",
        "GraphBFS.java",
        "GraphDFS.java",
        "KruskalsMST.java"
    ]

    # Copy each file into the destination folder
    for file_name in files_to_copy:
        source_file = current_dir / file_name
        destination_file = folder_path / file_name

        if source_file.exists():
            shutil.copy(source_file, destination_file)
        else:
            print(f"File '{file_name}' not found in the package directory.")
