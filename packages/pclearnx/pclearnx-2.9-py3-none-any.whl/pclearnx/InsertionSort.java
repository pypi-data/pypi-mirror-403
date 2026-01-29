package demo;
import java.util.Scanner;
public class InsertionSort {
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
		 for (int i = 1; i < n; i++) {
		 int k = a[i];
		 int j = i - 1;
		 while (j >= 0 && k < a[j]) {
		 a[j + 1] = a[j];
		 j = j - 1;
		 }
		 a[j + 1] = k;
		 }
		 System.out.print("\nsorted array is: ");
		 for (int i = 0; i < n; i++) {
		 System.out.print(a[i] + " ");
		 }
		
		 scanner.close();
	 }
	}
