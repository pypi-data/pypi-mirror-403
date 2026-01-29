package demo;
import java.util.Scanner;
public class CircularQueue {
	static int[] cqueue = new int[5];
	 static int front = -1, rear = -1, n = 3;
	 public static void insertCQ(int val) {
	 if ((front == 0 && rear == n - 1) || (front == rear + 1)) {
	 System.out.println("Queue Overflow");
	 return;
	 }
	 if (front == -1) {
	 front = 0;
	 rear = 0;
	 } else {
	 if (rear == n - 1)
	 rear = 0;
	 else
	 rear = rear + 1;
	 }
	 cqueue[rear] = val;
	 }
	 public static void deleteCQ() {
	 if (front == -1) {
	 System.out.println("Queue Underflow");
	 return;
	 }
	 System.out.println("Element deleted from queue is: " + cqueue[front]);
	 if (front == rear) {
		 front = -1;
		 rear = -1;
		 } else {
		 if (front == n - 1)
		 front = 0;
		 else
		 front = front + 1;
		 }}
		 public static void displayCQ() {
		 int f = front, r = rear;
		 if (front == -1) {
		 System.out.println("Queue is empty");
		 return;
		 }
		 System.out.println("Queue elements are:");
		 if (f <= r) {
		 while (f <= r) {
		 System.out.print(cqueue[f] + " ");
		 f++;
		 }
		 } else {
		 while (f <= n - 1) {
		 System.out.print(cqueue[f] + " ");
		 f++;
		 }
		 f = 0;
		 while (f <= r) {
		 System.out.print(cqueue[f] + " ");
		 f++;
		 }}
		 System.out.println();
		 }
		 public static void main(String[] args) {
		 System.out.println("sahabuddin 91");
		Scanner scanner = new Scanner(System.in);
		 int ch, val;
		 do {
		 System.out.println("1) Insert");
		 System.out.println("2) Delete");
		 System.out.println("3) Display");
		 System.out.println("4) Exit");
		 System.out.print("Enter choice: ");
		 ch = scanner.nextInt();
		 switch (ch) {
		 case 1:
		 System.out.print("Input for insertion: ");
		 val = scanner.nextInt();
		 insertCQ(val);
		 break;
		 case 2:
		 deleteCQ();
		 break;
		 case 3:
		 displayCQ();
		 break;
		 case 4:
		 System.out.println("Exit");
		 break;
		 default:
		 System.out.println("Incorrect choice!");
		 }
		 } while (ch != 4);
		 scanner.close();
		 }}
