package demo;

import java.util.Scanner;

class DequeNode {
    int data;
    DequeNode next;
    DequeNode prev;

    DequeNode(int value) {
        data = value;
        next = null;
        prev = null;
    }
}

class Deque {
    private DequeNode front;
    private DequeNode rear;

    public Deque() {
        front = rear = null;
    }

    public void insertFront(int value) {
        DequeNode newNode = new DequeNode(value);
        newNode.next = front;

        if (front != null) {
            front.prev = newNode;
        }

        front = newNode;

        if (rear == null) {
            rear = newNode;
        }

        System.out.println(value + " inserted at front");
    }

    public void insertRear(int value) {
        DequeNode newNode = new DequeNode(value);
        newNode.prev = rear;

        if (rear != null) {
            rear.next = newNode;
        }

        rear = newNode;

        if (front == null) {
            front = newNode;
        }

        System.out.println(value + " inserted at rear");
    }

    public int deleteFront() {
        if (front == null) {
            System.out.println("Deque is empty");
            return -1;
        }

        int value = front.data;
        front = front.next;

        if (front != null) {
            front.prev = null;
        } else {
            rear = null;
        }

        return value;
    }

    public int deleteRear() {
        if (rear == null) {
            System.out.println("Deque is empty");
            return -1;
        }

        int value = rear.data;
        rear = rear.prev;

        if (rear != null) {
            rear.next = null;
        } else {
            front = null;
        }

        return value;
    }

    public void display() {
        if (front == null) {
            System.out.println("Deque is empty");
            return;
        }

        DequeNode current = front;
        System.out.print("Deque contents: ");

        while (current != null) {
            System.out.print(current.data + " ");
            current = current.next;
        }

        System.out.println();
    }
}

public class DoubleEndedQueueLinkedList {
    public static void main(String[] args) {

        Deque dq = new Deque();
        Scanner scanner = new Scanner(System.in);

        int ch, value;

        do {
            System.out.println("\nDeque Operations Menu:");
            System.out.println("1. Insert Front");
            System.out.println("2. Insert Rear");
            System.out.println("3. Delete Front");
            System.out.println("4. Delete Rear");
            System.out.println("5. Display");
            System.out.println("6. Exit");

            System.out.print("Enter your choice: ");
            ch = scanner.nextInt();

            switch (ch) {

                case 1:
                    System.out.print("Enter value to insert at front: ");
                    value = scanner.nextInt();
                    dq.insertFront(value);
                    break;

                case 2:
                    System.out.print("Enter value to insert at rear: ");
                    value = scanner.nextInt();
                    dq.insertRear(value);
                    break;

                case 3:
                    value = dq.deleteFront();
                    if (value != -1)
                        System.out.println(value + " deleted from front");
                    break;

                case 4:
                    value = dq.deleteRear();
                    if (value != -1)
                        System.out.println(value + " deleted from rear");
                    break;

                case 5:
                    dq.display();
                    break;

                case 6:
                    System.out.println("Exiting...");
                    System.exit(0);

                default:
                    System.out.println("Invalid choice. Try again.");
            }

        } while (ch != 6);

        scanner.close();
    }
}
