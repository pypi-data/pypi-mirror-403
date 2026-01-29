package demo;

import java.util.Scanner;

class PQNode {
    int data;
    int priority;
    PQNode next;

    PQNode(int data, int priority) {
        this.data = data;
        this.priority = priority;
        this.next = null;
    }
}

class PriorityQueue {
    private PQNode front;

    public PriorityQueue() {
        front = null;
    }

    public void enqueue(int value, int priority) {
        PQNode newNode = new PQNode(value, priority);

        if (front == null || priority < front.priority) {
            newNode.next = front;
            front = newNode;
        } else {
            PQNode current = front;

            while (current.next != null && current.next.priority <= priority) {
                current = current.next;
            }

            newNode.next = current.next;
            current.next = newNode;
        }

        System.out.println(value + " enqueued with priority " + priority);
    }

    public int dequeue() {
        if (front == null) {
            System.out.println("Queue is empty");
            return -1;
        }

        int value = front.data;
        front = front.next;
        return value;
    }

    public void display() {
        if (front == null) {
            System.out.println("Queue is empty");
            return;
        }

        PQNode current = front;
        System.out.print("Priority Queue (data:priority): ");

        while (current != null) {
            System.out.print("(" + current.data + ":" + current.priority + ") ");
            current = current.next;
        }

        System.out.println();
    }
}

public class Priority_Queue {
    public static void main(String[] args) {
        PriorityQueue pq = new PriorityQueue();
        Scanner scanner = new Scanner(System.in);

        int ch, value, priority;

        do {
            System.out.println("\n--- Priority Queue Menu ---");
            System.out.println("1. Enqueue");
            System.out.println("2. Dequeue");
            System.out.println("3. Display");
            System.out.println("4. Exit");
            System.out.print("Enter your choice: ");

            ch = scanner.nextInt();

            switch (ch) {
                case 1:
                    System.out.print("Enter value to enqueue: ");
                    value = scanner.nextInt();

                    System.out.print("Enter priority (lower number = higher priority): ");
                    priority = scanner.nextInt();

                    pq.enqueue(value, priority);
                    break;

                case 2:
                    value = pq.dequeue();
                    if (value != -1) {
                        System.out.println(value + " dequeued from queue");
                    }
                    break;

                case 3:
                    pq.display();
                    break;

                case 4:
                    System.out.println("Exiting...");
                    System.exit(0);

                default:
                    System.out.println("Invalid choice! Try again.");
            }

        } while (ch != 4);

        scanner.close();
    }
}

