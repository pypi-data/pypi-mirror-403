package demo;
import java.util.Scanner;

public class HeapOperations {
    static int[] array1 = new int[100];
    static int n = 0;

    public static void display() {
        if (n == 0) {
            System.out.println("Heap is empty");
            return;
        }
        for (int i = 0; i < n; i++) {
            System.out.print(array1[i] + "\t");
        }
        System.out.println();
    }

    public static void insert1(int num, int location) {
        int parentnode;
        while (location > 0) {
            parentnode = (location - 1) / 2;
            if (num <= array1[parentnode]) {
                array1[location] = num;
                return;
            }
            array1[location] = array1[parentnode];
            location = parentnode;
        }
        array1[0] = num;
    }

    public static void delete1(int num) {
        int left, right, i, temp, parentnode;
        for (i = 0; i < n; i++) {
            if (num == array1[i]) {
                break;
            }
        }
        if (num != array1[i]) {
            System.out.println(num + " not found in heap list");
            return;
        }

        array1[i] = array1[n - 1];
        n = n - 1;
        parentnode = (i - 1) / 2;

        if (array1[i] > array1[parentnode]) {
            insert1(array1[i], i);
            return;
        }

        left = 2 * i + 1;
        right = 2 * i + 2;

        while (right < n) {
            if (array1[i] >= array1[left] && array1[i] >= array1[right]) {
                return;
            }
            if (array1[right] <= array1[left]) {
                temp = array1[i];
                array1[i] = array1[left];
                array1[left] = temp;
                i = left;
            } else {
                temp = array1[i];
                array1[i] = array1[right];
                array1[right] = temp;
                i = right;
            }
            left = 2 * i + 1;
            right = 2 * i + 2;
        }

        if (left == n - 1 && array1[i] < array1[left]) {
            temp = array1[i];
            array1[i] = array1[left];
            array1[left] = temp;
        }
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int choice, num;

        while (true) {
            System.out.println("1. Insert the element");
            System.out.println("2. Delete the element");
            System.out.println("3. Display all elements");
            System.out.println("4. Quit");
            System.out.print("Enter your choice: ");
            choice = scanner.nextInt();

            switch (choice) {
                case 1:
                    System.out.print("Enter the element to be inserted to the list: ");
                    num = scanner.nextInt();
                    insert1(num, n);
                    n = n + 1;
                    break;
                case 2:
                    System.out.print("Enter the element to be deleted from the list: ");
                    num = scanner.nextInt();
                    delete1(num);
                    break;
                case 3:
                    display();
                    break;
                case 4:
                	scanner.close();
                    System.exit(0);
                    break;
                default:
                    System.out.println("Invalid choice");
            }
        }
    }
}
