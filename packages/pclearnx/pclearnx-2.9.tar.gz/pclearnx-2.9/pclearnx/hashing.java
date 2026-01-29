package demo;
import java.util.Scanner;

public class hashing {
   public static int hashSearch(int[] hashTable, int x, int n) {
       int index = x % n;
       int start = index;
       if (hashTable[index] == x) {
           return index;
       } else if (hashTable[index] == -1) {
           return -1;
       } else {
           do {
               index = (index + 1) % n;
               if (hashTable[index] == x) {
                   return index;
               } else if (hashTable[index] == -1) {
                   break;
               }
           } while (index != start);
           return -1;
       }
   }

   public static void main(String[] args) {
       Scanner scanner = new Scanner(System.in);
       int[] hashTable = new int[10];
       int i, x, index, k;

       for (i = 0; i < 10; i++) {
           hashTable[i] = -1;
       }

       System.out.println("Hashing using linear probing\n");
       System.out.println("Hash table creation\n");

       for (i = 1; i <= 7; i++) {
           System.out.print("Enter a number: ");
           x = scanner.nextInt();
           index = x % 10;
           while (hashTable[index] != -1) {
               index = (index + 1) % 10;
           }
           hashTable[index] = x;
       }

       System.out.println("\nHASH TABLE");
       for (i = 0; i < 10; i++) {
           System.out.print(i + " ");
       }
       System.out.println();

       for (i = 0; i < 10; i++) {
           System.out.print(hashTable[i] + " ");
       }

       do {
           System.out.print("\nElement to be searched (enter -1 to stop): ");
           x = scanner.nextInt();
           if (x >= 0) {
               k = hashSearch(hashTable, x, 10);
               if (k >= 0) {
                   System.out.println(x + " is present at hash[" + k + "]");
               } else {
                   System.out.println(x + " is not present");
               }
           }
       } while (x >= 0);

       scanner.close();
   }
}
