package demo;
import java.util.Scanner;
public class BubbleSort {
	public static void main(String[] args) {
		 Scanner scanner = new Scanner(System.in);
		 System.out.print("How many elements you want to add: ");
		 int n = scanner.nextInt();
		 int[] a = new int[n];
		 for (int i = 0; i < n; i++) {
		 System.out.print("Enter the elements: ");
		 a[i] = scanner.nextInt();
		 }
		 System.out.print("Given array is: ");
		 for (int i = 0; i < n; i++) {
		 System.out.print(a[i] + " ");
		 }
		 for (int i = 0; i < n - 1; i++) {
		 for (int j = 0; j < n - i - 1; j++) {
		 if (a[j] > a[j + 1]) {
		 int temp = a[j];
		 a[j] = a[j + 1];
		 a[j + 1] = temp;
		 }
		 }
		 }
		 System.out.println("\n");
		 System.out.print("sorted array is: ");
		 for (int i = 0; i < n; i++) {
			 System.out.print(a[i] + " ");
			 }
			 scanner.close();
			 }
			}
