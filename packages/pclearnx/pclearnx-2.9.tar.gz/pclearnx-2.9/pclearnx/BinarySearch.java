  package demo;
       import java.util.Scanner;
       public class BinarySearch {
	 public static void main(String[] args) {
		 Scanner scanner = new Scanner(System.in);
		 System.out.print("how many number you want to insert: ");
		 int n = scanner.nextInt();
		 int[] a = new int[n];
		 System.out.println("Enter the sorted array: ");
		 for (int i = 0; i < n; i++) {
		 System.out.print("Enter the number: ");
		 a[i] = scanner.nextInt();
		 }
		 System.out.print("Array: ");
		 for (int i = 0; i < n; i++) {
		 System.out.print(a[i] + " ");
		 }
		 System.out.print("\nenter the number you want to search: ");
		 int x = scanner.nextInt();
		 int low = 0, high = n - 1;
		 int flag = 0;
		 while (low <= high) {
		 int mid = low + (high - low) / 2;
		 if (a[mid] == x) {
		 flag = 1;
		 break;
		 }
		 if (a[mid] > x) {
		 high = mid - 1;
      }
		 if (a[mid] > x) {
			 high = mid - 1;
		 } else {
			 low = mid + 1;
			 }
			 }
			 if (flag == 1) {
			 System.out.println("number found");
			 } else {
			 System.out.println("number not found");
			 }
			 scanner.close();
			 }
			}
