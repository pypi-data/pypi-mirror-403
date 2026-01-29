package demo;
import java.util.Scanner;
public class SelectionSort {

	public static void main(String[] args) {
		 int i, n, j, temp, min;
		 System.out.print("How many elements you want to add: ");
		 Scanner scanner = new Scanner(System.in);
		 n = scanner.nextInt();
		 int[] a = new int[n];
		 for (i = 0; i < n; i++) {
		 System.out.print("Enter the elements: ");
		 a[i] = scanner.nextInt();
		 }
		 System.out.print("Given array is: ");
		 for (i = 0; i < n; i++) {
		 System.out.print(a[i] + " ");
		 }
		 for (i = 0; i < n; i++) {
		 min = i;
		 for (j = i + 1; j < n; j++) {
		 if (a[min] > a[j]) {
		 min = j;
		 }
		 }
		 if (a[min] != a[i]) {
		 temp = a[i];
		 a[i] = a[min];
		 a[min] = temp;
		 }
		 }
		 System.out.print("\n Sorted array is: ");
		 for (i = 0; i < n; i++) {
		 System.out.print(a[i] + " ");
		 }
		 }
		}
