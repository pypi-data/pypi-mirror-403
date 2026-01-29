package demo;

import java.util.Scanner;

public class LinearSearch {
	public static void main(String[] args) {
	int i, x, n;
	int flag = 0;
	Scanner scanner = new Scanner(System.in);
	System.out.println("How many numbers you want to enter in the array:");
	n = scanner.nextInt();
	int[] a = new int[n];
	for (i = 0; i < n; i++) {
	System.out.println("Enter Element:");
	a[i] = scanner.nextInt();
	}
	System.out.println("Enter number which you want to search:");
	x = scanner.nextInt();
	for (i = 0; i < n; i++) {
	if (a[i] == x) {
	flag = 1;
	break;
}
}
if (flag == 1) {
System.out.println("Element Found!");
} else {

System.out.println("Element not found!");
}
	scanner.close();
}
}
