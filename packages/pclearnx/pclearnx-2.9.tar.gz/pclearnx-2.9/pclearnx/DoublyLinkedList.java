package demo;
import java.util.Scanner; 

public class DoublyLinkedList { 

    class Node { 
        int data; 
        Node next; 
        Node prev; 
    } 

    private Node tmp = null; 
    private Node ptr = null; 
    private Node start = null; 
    private Node p = null; 
    private Node p1 = null; 
    private Node p2 = null; 

    // Create node at end 
    public void create(int x) { 
        tmp = new Node(); 
        tmp.data = x; 
        tmp.next = null; 

        if (start == null) { 
            tmp.prev = null; 
            start = tmp; 
        } else { 
            p = start; 
            while (p.next != null) { 
                p = p.next; 
            } 
            p.next = tmp; 
            tmp.prev = p; 
        } 
    } 

    // Add at beginning 
    public void addAtBegin(int x) { 
        if (start == null) { 
            System.out.println("List is empty.\n"); 
        } 
        tmp = new Node(); 
        tmp.data = x; 
        tmp.next = start; 

        if (start != null) 
            start.prev = tmp; 

        start = tmp; 
    } 

    // Add after a given position 
    public void addAfter(int x, int pos) { 
        if (start == null) { 
            System.out.println("List is empty.\n"); 
            return; 
        } 

        p = start; 
        for (int i = 0; i < pos - 1; i++) { 
            p = p.next; 
            if (p == null) { 
                System.out.println("Position does not exist.\n"); 
                return; 
            } 
        } 

        tmp = new Node(); 
        tmp.data = x; 

        if (p.next == null) { 
            p.next = tmp; 
            tmp.prev = p; 
            tmp.next = null; 
        } else { 
            tmp.next = p.next; 
            p.next.prev = tmp; 
            p.next = tmp; 
            tmp.prev = p; 
        } 
    } 

    // Delete a specific element 
    public void del(int x) { 
        if (start == null) { 
            System.out.println("List is empty.\n"); 
            return; 
        } 

        // Delete first node 
        if (start.data == x) { 
            tmp = start; 
            if (start.next == null) { 
                start = null; 
            } else { 
                start = start.next; 
                start.prev = null; 
            } 
            return; 
        } 

        // Delete in between or last 
        p = start; 
        while (p != null) { 
            if (p.data == x) { 
                if (p.next != null) { 
                    p.next.prev = p.prev; 
                } 
                if (p.prev != null) { 
                    p.prev.next = p.next; 
                } 
                return; 
            } 
            p = p.next; 
        } 

        System.out.println("Element not found."); 
    } 

    // Reverse the list 
    public void reverse() { 
        if (start == null) { 
            System.out.println("List is empty.\n"); 
            return; 
        } 

        p1 = start; 
        p2 = p1.next; 
        p1.next = null; 
        p1.prev = p2; 

        while (p2 != null) { 
            p2.prev = p2.next; 
            p2.next = p1; 
            p1 = p2; 
            p2 = p2.prev; 
        } 

        start = p1; 
        System.out.println("List reversed."); 
    } 

    // Count nodes 
    public void count() { 
        p = start; 
        int cnt = 0; 

        while (p != null) { 
            cnt++; 
            p = p.next; 
        } 

        System.out.println("Number of elements are " + cnt + "."); 
    } 

    // Search element 
    public void search() { 
        int count = 0; 
        int value; 
        int flag = 0; 

        Scanner sc = new Scanner(System.in); 
        System.out.println("Enter the element to be searched:"); 
        value = sc.nextInt(); 

        if (start == null) { 
            System.out.println("List is empty.\n"); 
            return; 
        } 

        p = start; 
        while (p != null) { 
            count++; 
            if (p.data == value) { 
                flag = 1; 
                System.out.println("Element found at position " + count + "."); 
            } 
            p = p.next; 
        } 

        if (flag == 0) { 
            System.out.println("Element not found."); 
        } 
    } 

    // Sort list 
    public void sort() { 
        if (start == null) { 
            System.out.println("List is empty.\n"); 
            return; 
        } 

        ptr = start; 
        while (ptr != null) { 
            for (p = ptr.next; p != null; p = p.next) { 
                if (ptr.data > p.data) { 
                    int x = ptr.data; 
                    ptr.data = p.data; 
                    p.data = x; 
                } 
            } 
            ptr = ptr.next; 
        } 
    } 

    // Display list 
    public void display() { 
        if (start == null) { 
            System.out.println("List is empty.\n"); 
            return; 
        } 

        p = start; 
        System.out.println("\nDoubly Linked List:"); 
        while (p != null) { 
            System.out.print(p.data + " -> "); 
            p = p.next; 
        } 
        System.out.println("\n"); 
    } 

    // Main function 
    public static void main(String[] args) { 

        DoublyLinkedList d = new DoublyLinkedList(); 
        Scanner sc = new Scanner(System.in); 

        int x, ch, pos; 

        while (true) { 

            System.out.println("1. Create a list"); 
            System.out.println("2. Add at begin"); 
            System.out.println("3. Add after"); 
            System.out.println("4. Search"); 
            System.out.println("5. Reverse"); 
            System.out.println("6. Count"); 
            System.out.println("7. Sort"); 
            System.out.println("8. Display"); 
            System.out.println("9. Delete"); 
            System.out.println("10. Exit"); 

            System.out.print("\nEnter your choice: "); 
            ch = sc.nextInt(); 

            switch (ch) { 

                case 1: 
                    System.out.print("Enter the value: "); 
                    x = sc.nextInt(); 
                    d.create(x); 
                    d.display(); 
                    break; 

                case 2: 
                    System.out.print("Enter the value: "); 
                    x = sc.nextInt(); 
                    d.addAtBegin(x); 
                    d.display(); 
                    break; 

                case 3: 
                    System.out.print("Enter position: "); 
                    pos = sc.nextInt(); 
                    System.out.print("Enter value: "); 
                    x = sc.nextInt(); 
                    d.addAfter(x, pos); 
                    d.display(); 
                    break; 

                case 4: 
                    d.search(); 
                    break; 

                case 5: 
                    d.reverse(); 
                    d.display(); 
                    break; 

                case 6: 
                    d.count(); 
                    break; 

                case 7: 
                    System.out.print("Before sorting - "); 
                    d.display(); 
                    d.sort(); 
                    System.out.print("After sorting - "); 
                    d.display(); 
                    break; 

                case 8: 
                    d.display(); 
                    break; 

                case 9: 
                    System.out.print("Enter element to delete: "); 
                    x = sc.nextInt(); 
                    d.del(x); 
                    d.display(); 
                    break; 

                case 10: 
                    sc.close(); 
                    return; 

                default: 
                    System.out.println("Wrong choice.\n"); 
            } 
        } 
    } 
} 
