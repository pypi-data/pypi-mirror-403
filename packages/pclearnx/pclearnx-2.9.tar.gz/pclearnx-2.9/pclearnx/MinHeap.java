package demo;
import java.util.Scanner;

public class MinHeap {

    public static void minHeapify(int[] a, int i, int n) {
        int j, temp;
        temp = a[i];
        j = 2 * i;

        while (j <= n) {
            if (j < n && a[j + 1] < a[j]) {
                j = j + 1;
            }
            if (temp < a[j]) {
                break;
            } else if (temp >= a[j]) {
                a[j / 2] = a[j];
                j = 2 * j;
            }
        }
        a[j / 2] = temp;
    }

    public static void buildMinHeap(int[] a, int n) {
        for (int i = n / 2; i >= 1; i--) {
            minHeapify(a, i, n);
        }
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.println("Enter number of elements in the array:");

        int n = scanner.nextInt();
        int[] a = new int[21];

        for (int i = 1; i <= n; i++) {
            System.out.println("Enter element " + i + ":");
            a[i] = scanner.nextInt();
        }

        buildMinHeap(a, n);

        System.out.println("Min Heap:");
        for (int i = 1; i <= n; i++) {
            System.out.println(a[i]);
        }

        scanner.close();
    }
}
