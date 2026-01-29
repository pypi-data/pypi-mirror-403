package demo;

import java.util.Scanner;

public class CircularLinkedList {
	boolean flag = true; 
    int pos, i, value, count = 0; 
    Node tmp = null; 
    Node start = null; 
    Node last = null; 
    Node p = null; 
    Node ptr = null; 

    class Node { 
        int data; 
        Node next; 
        Node prev; 
    } 

    // Create node at end 
    void create(int x) { 
        tmp = new Node(); 
        tmp.data = x; 

        if (last == null) { 
            last = tmp; 
            tmp.next = last; 
        } else { 
            tmp.next = last.next; 
            last.next = tmp; 
            last = tmp; 
        } 
    } 

    // Add at beginning 
    void addAtBegin(int x) { 
        if (last == null) { 
            System.out.println("List is empty."); 
            return; 
        } 

        tmp = new Node(); 
        tmp.data = x; 
        tmp.next = last.next; 
        last.next = tmp; 
    } 

    // Add after a given position 
    void addAfter(int x, int pos) { 
        if (last == null) { 
            System.out.println("List is empty."); 
            return; 
        } 

        p = last.next; 
        for (i = 0; i < pos - 1; i++) { 
            p = p.next; 
            if (p == last.next) { 
                System.out.println("Position does not exist."); 
                return; 
            } 
        } 

        tmp = new Node(); 
        tmp.data = x; 
        tmp.next = p.next; 
        p.next = tmp; 

        if (p == last) { 
            last = tmp; 
        } 
    } 

    // Delete a node with specific value 
    void del(int x) { 

        if (last == null) { 
            System.out.println("List is empty."); 
            return; 
        } 

        // Only one node 
        if (last.next == last && last.data == x) { 
            tmp = last; 
            last = null; 
            return; 
        } 

        p = last.next; 

        // Delete first node 
        if (p.data == x) { 
            tmp = p; 
            last.next = p.next; 
            return; 
        } 

        // Delete node in between 
        while (p.next != last) { 
            if (p.next.data == x) { 
                tmp = p.next; 
                p.next = tmp.next; 
                return; 
            } 
            p = p.next; 
        } 

        // Delete last node 
        if (p.next.data == x) { 
            tmp = p.next; 
            p.next = last.next; 
            last = p; 
            return; 
        } 

        System.out.println("Element not found."); 
    } 

    // Search element 
    void search1(int x) { 
        int pos = 1; 

        if (last == null) { 
            System.out.println("List is empty."); 
            return; 
        } 

        p = last.next; 

        do { 
            if (p.data == x) { 
                System.out.println("Element found at position " + pos + "."); 
                return; 
            } 
            p = p.next; 
            pos++; 
        } while (p != last.next); 

        System.out.println("Item not found."); 
    } 

    // Sort list 
    void sort() { 
        int x; 

        if (last == null) { 
            System.out.println("List is empty."); 
            return; 
        } 

        p = last.next; 

        while (p != last) { 
            ptr = p.next; 

            while (ptr != last.next) { 
                if (p.data > ptr.data) { 
                    x = p.data; 
                    p.data = ptr.data; 
                    ptr.data = x; 
                } 
                ptr = ptr.next; 
            } 
            p = p.next; 
        } 
    } 

    // Count nodes 
    void count1() { 
        if (last == null) { 
            System.out.println("List is empty."); 
            return; 
        } 

        count = 0; 
        p = last.next; 

        do { 
            count++; 
            p = p.next; 
        } while (p != last.next); 

        System.out.println("Number of elements are " + count); 
    } 

    // Display list 
    void display() { 
        if (last == null) { 
            System.out.println("List is empty."); 
            return; 
        } 

        p = last.next; 

        System.out.println("\nSingly Circular Linked List:"); 
        while (p != last) { 
            System.out.print(p.data + " -> "); 
            p = p.next; 
        } 
        System.out.println(last.data + " -> (back to start)\n"); 
    } 
 
    public static void main(String[] args) { 

    	CircularLinkedList d = new CircularLinkedList(); 
        Scanner sc = new Scanner(System.in); 

        int x, ch, pos; 

        while (true) { 

            System.out.println("1. Create a list"); 
            System.out.println("2. Add at begin"); 
            System.out.println("3. Add after"); 
            System.out.println("4. Search"); 
            System.out.println("5. Sort"); 
            System.out.println("6. Count"); 
            System.out.println("7. Display"); 
            System.out.println("8. Delete"); 
            System.out.println("9. Exit"); 
            System.out.print("Enter the choice:\n"); 

            ch = sc.nextInt(); 

            switch (ch) { 

                case 1: 
                    System.out.print("Enter the value:\n"); 
                    x = sc.nextInt(); 
                    d.create(x); 
                    d.display(); 
                    break; 

                case 2: 
                    System.out.print("Enter the value:\n"); 
                    x = sc.nextInt(); 
                    d.addAtBegin(x); 
                    d.display(); 
                    break; 

                case 3: 
                    System.out.print("Enter the position:\n"); 
                    pos = sc.nextInt(); 
                    System.out.print("Enter the value:\n"); 
                    x = sc.nextInt(); 
                    d.addAfter(x, pos); 
                    d.display(); 
                    break; 

                case 4: 
                    System.out.print("Enter element to be searched:\n"); 
                    x = sc.nextInt(); 
                    d.search1(x); 
                    break; 

                case 5: 
                    System.out.println("Before sorting:"); 
                    d.display(); 
                    d.sort(); 
                    System.out.println("After sorting:"); 
                    d.display(); 
                    break; 

                case 6: 
                    d.count1(); 
                    break; 

                case 7: 
                    d.display(); 
                    break; 

                case 8: 
                    System.out.print("Enter the element to be deleted:\n"); 
                    x = sc.nextInt(); 
                    d.del(x); 
                    d.display(); 
                    break; 

                case 9: 
                    sc.close(); 
                    return; 

                default: 
                    System.out.println("Wrong choice."); 
            } 
        } 
    } 
} 

