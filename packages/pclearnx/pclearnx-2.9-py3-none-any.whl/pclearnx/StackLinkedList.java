package demo;

import java.util.Scanner;

class Node {
    int data;
    Node next;

    Node(int data) {
        this.data = data;
        this.next = null;
    }
}

class MyStack {
    private Node top = null;

    public void push(int x) {
        Node ptr = new Node(x);
        if (top != null) {
            ptr.next = top;
        }
        top = ptr;
    }

    public void pop() {
        if (top == null) {
            System.out.println("\nStack is empty.");
        } else {
            Node temp = top;
            top = top.next;
            System.out.println("Popped value : " + temp.data);
        }
    }

    public void display() {
        Node ptr1 = top;

        if (top == null) {
            System.out.println("Stack is empty.\n");
        } else {
            System.out.println("Stack :");
            while (ptr1 != null) {
                System.out.println(ptr1.data);
                ptr1 = ptr1.next;
            }
        }
    }
}

public class StackLinkedList {
    public static void main(String[] args) {

        MyStack s = new MyStack();
        int ch = 0, x;

        Scanner scanner = new Scanner(System.in);

        while (ch != 4) {
            System.out.println("1. Push");
            System.out.println("2. Pop");
            System.out.println("3. Display");
            System.out.println("4. Exit");
            System.out.print("Enter your choice : ");
            ch = scanner.nextInt();

            switch (ch) {
                case 1:
                    System.out.print("Enter the value : ");
                    x = scanner.nextInt();
                    s.push(x);
                    break;

                case 2:
                    s.pop();
                    break;

                case 3:
                    s.display();
                    break;

                case 4:
                    System.out.println("Exiting...");
                    break;

                default:
                    System.out.println("\nWrong choice.\n");
            }
        }

        scanner.close();
    }
}

