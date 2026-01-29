package demo;

import java.util.Scanner;

class QueueNode {
    int data;
    QueueNode next;

    QueueNode(int data) {
        this.data = data;
        this.next = null;
    }
}

class LinkQueue {
    private QueueNode front = null;
    private QueueNode rear = null;

    public void enqueue(int x) {
        QueueNode tmp = new QueueNode(x);

        if (front == null && rear == null) {
            front = rear = tmp;
        } else {
            rear.next = tmp;
            rear = tmp;
        }
    }

    public void dequeue() {
        if (front == null) {
            System.out.println("Queue is empty\n");
            return;
        }

        System.out.println("Deleted : " + front.data);

        if (front == rear) {
            front = rear = null;
        } else {
            front = front.next;
        }
    }

    public void display() {
        if (front == null) {
            System.out.println("Queue is empty.\n");
        } else {
            QueueNode ptr = front;
            System.out.println("Queue :");

            while (ptr != null) {
                System.out.print(ptr.data + "\t");
                ptr = ptr.next;
            }

            System.out.println();
        }
    }
}

public class Linked_Queue {
    public static void main(String[] args) {

        LinkQueue q = new LinkQueue();
        Scanner scanner = new Scanner(System.in);
        int ch, x;

        do {
            System.out.println("\n1. Enqueue");
            System.out.println("2. Dequeue");
            System.out.println("3. Display");
            System.out.println("4. Exit");
            System.out.print("Enter your choice: ");

            ch = scanner.nextInt();

            switch (ch) {
                case 1:
                    System.out.print("Enter the value: ");
                    x = scanner.nextInt();
                    q.enqueue(x);
                    break;

                case 2:
                    q.dequeue();
                    break;

                case 3:
                    q.display();
                    break;

                case 4:
                    System.out.println("Exiting...");
                    break;

                default:
                    System.out.println("\nWrong choice.\n");
            }
        } while (ch != 4);

        scanner.close();
    }
}

