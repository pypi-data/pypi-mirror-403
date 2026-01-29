package demo;
import java.util.Scanner;
public class ShellSort {
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
		 System.out.println();
		 for (int i = n / 2; i > 0; i /= 2) {
		 int flag = 1;
		 while (flag == 1) {
		 flag = 0;
		 for (int j = 0; j < n - i; j++) {
		 if (a[j] > a[j + i]) {
		 int temp = a[j];
		 a[j] = a[j + i];
		 a[j + i] = temp;
		 flag = 1;
		 }
		 }
		 }
		 }
		 System.out.print("sorted array is: ");
		 for (int i = 0; i < n; i++) {
		 System.out.print(a[i] + " ");
		 }
		 }
		}

