package demo;
import java.util.Scanner;
public class StackArray {
	int top = -1;
	 int x, stk[] = new int[5], i;
	 int MAX = 5;
	 public void push(int x) {
	 if (top == MAX - 1) {
	 System.out.println("Stack Overflow\n");
	 } else {
	 System.out.println("Enter the number to push to the stack:");
	 Scanner sc = new Scanner(System.in);
	 x = sc.nextInt();
	 stk[++top] = x;
	 stk[top] = x;
	 }
	 }
	 public void pop() {
	 if (top == -1) {
	 System.out.println("Stack Underflow\n");
	 }
	 System.out.print("Popped value: ");
	 x = stk[top];
	 top--;
	 System.out.println(x);
	 }
	 public void display() {
		if (top == -1) {
		 System.out.println("Stack is empty.\n");
		 } 
		 else {
		  System.out.println("Stack:");
		 for (i = top; i >= 0; i--) {
		  System.out.println(stk[i]);
		 }
	} } 
		 public static void main(String[] args) {
		 StackArray s = new StackArray();
		 int ch, x = 0;
		 Scanner sc = new Scanner(System.in);
		 while (true) {
		 System.out.println("1.Push\n2.Pop\n3.Display\n4.Exit");
		 System.out.print("Enter the value for operation:\n");
		 ch = sc.nextInt();
		 switch (ch) {
		 case 1:
		 s.push(x);
		 break;
		 case 2:
		 s.pop();
		 break;
		 case 3:
		 s.display();
		 break;
		 case 4:
		 return;
		 default:
			 System.out.println("\nWrong choice.\n");
		 } 
	}
}
}
