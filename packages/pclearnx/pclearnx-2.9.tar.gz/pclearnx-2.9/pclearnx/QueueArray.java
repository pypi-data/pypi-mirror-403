package demo;

import java.util.Scanner;

public class QueueArray {
	private int front = -1, rear = -1;
    private int[] queue;
    private final int MAX = 3;
    public QueueArray() {
    queue = new int[MAX];
   }
    public void enqueue(Scanner scanner) {
   if (rear == MAX - 1) {
   System.out.println("Queue Overflow\n");
   } else {
   if (front == -1) {
   front = 0;
   }
   System.out.println("Enter the number to enqueue to the queue:");
   int x = scanner.nextInt();
   queue[++rear] = x;
    }}
    public void dequeue() {
    if (front == -1 || front > rear) {
    System.out.println("Queue Underflow\n");
    return;
   }
   System.out.println("Dequeued value: " + queue[front] + "\n");
   front++;
   }
    public void display() {
    if (front == -1 || front > rear) {
    System.out.println("Queue is empty.\n");
    } else {
    System.out.println("Queue:");
    for (int i = front; i <= rear; i++) {
    System.out.print(queue[i] + " ");
    }
    System.out.println();
    }
    }
    public static void main(String[] args) {
    QueueArray q = new QueueArray();
    Scanner scanner = new Scanner(System.in);
    int ch = 0;
    while (ch != 4) {
    System.out.println(" 1.Enqueue\n 2.Dequeue\n 3.Display\n 4.Exit");
    System.out.println("Enter the value for operation:");
    ch = scanner.nextInt();
    switch (ch) {
    case 1:
    q.enqueue(scanner);
    break;
    case 2:
    q.dequeue();
    break;
    case 3:
    q.display();
    break;
    case 4:
    break;
    default:
    System.out.println("\nWrong choice.\n");
    }
    }
    scanner.close();
    }}
