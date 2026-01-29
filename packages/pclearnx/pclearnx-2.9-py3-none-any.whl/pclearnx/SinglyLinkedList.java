package demo;

import java.util.Scanner;

public class SinglyLinkedList {
    static Scanner scanner = new Scanner(System.in);

    int flag;
    int pos, i, value, count1 = 0;
    Node start = null;

    class Node {
        int data;
        Node next;
    }

    public int countNodes() {
        int count = 0;
        Node p = start;
        while (p != null) {
            count++;
            p = p.next;
        }
        return count;
    }

    public void insertAtBeg(int x) {
        Node tmp = new Node();
        tmp.data = x;
        tmp.next = start;
        start = tmp;
    }

    public void insertAtEnd(int x) {
        Node tmp = new Node();
        tmp.data = x;
        tmp.next = null;

        if (start == null) {
            start = tmp;
        } else {
            Node p = start;
            while (p.next != null) {
                p = p.next;
            }
            p.next = tmp;
        }
    }

    public void insertAtPos(int x) {
        System.out.println("Insert the position:");
        pos = scanner.nextInt();

        int count = countNodes();

        if (pos == 1) {
            insertAtBeg(x);
        } else if (pos > 1 && pos <= count + 1) {
            Node tmp = new Node();
            tmp.data = x;

            Node p = start;
            for (i = 1; i < pos - 1; i++) {
                p = p.next;
            }

            tmp.next = p.next;
            p.next = tmp;
        } else {
            System.out.println("Invalid position.");
        }
    }

    public void searchPos() {
        System.out.println("Insert the value to search:");
        value = scanner.nextInt();

        count1 = 0;
        flag = 0;

        if (start == null) {
            System.out.println("List is empty");
        } else {
            Node p = start;

            while (p != null) {
                count1++;

                if (p.data == value) {
                    flag = 1;
                    System.out.println("Value found at position " + count1);
                    break;
                }

                p = p.next;
            }

            if (flag == 0) {
                System.out.println("Value not found");
            }
        }
    }

    public void del() {
        System.out.println("Delete the position:");
        pos = scanner.nextInt();

        int count = countNodes();

        if (start == null) {
            System.out.println("List is empty.");
        } else if (pos == 1) {
            start = start.next;
        } else if (pos > 1 && pos <= count) {
            Node p = start;
            Node ptr = null;

            for (i = 1; i < pos; i++) {
                ptr = p;
                p = p.next;
            }
            ptr.next = p.next;

        } else {
            System.out.println("Invalid position.");
        }
    }

    public void sort() {
        if (start == null) {
            System.out.println("List is empty.");
        } else {
            Node ptr = start;

            while (ptr != null) {
                Node p = ptr.next;

                while (p != null) {
                    if (ptr.data > p.data) {
                        int temp = ptr.data;
                        ptr.data = p.data;
                        p.data = temp;
                    }
                    p = p.next;
                }

                ptr = ptr.next;
            }
        }
    }

    public void rev() {
        if (start == null) {
            System.out.println("List is empty.");
        } else {
            Node prev = null;
            Node curr = start;
            Node next = null;

            while (curr != null) {
                next = curr.next;
                curr.next = prev;
                prev = curr;
                curr = next;
            }

            start = prev;
        }
    }

    public void display() {
        if (start == null) {
            System.out.println("List is empty.");
        } else {
            Node p = start;
            System.out.println("\nSingly Linked List:");

            while (p != null) {
                System.out.print(p.data + " -> ");
                p = p.next;
            }

            System.out.println("null");
        }
    }

    public static void main(String[] args) {
        SinglyLinkedList l = new SinglyLinkedList();

        int ch = -1;

        while (ch != 0) {
            System.out.println(
                "1.Insert at beginning\n2.Insert at end\n3.Insert at position\n4.Delete\n5.Search\n6.Display\n7.Sort\n8.Reverse\n9.Exit"
            );
            System.out.println("Enter the choice:");
            ch = scanner.nextInt();

            switch (ch) {

                case 1:
                    System.out.println("Enter the value");
                    int x1 = scanner.nextInt();
                    l.insertAtBeg(x1);
                    l.display();
                    break;

                case 2:
                    System.out.println("Enter the value");
                    int x2 = scanner.nextInt();
                    l.insertAtEnd(x2);
                    l.display();
                    break;

                case 3:
                    System.out.println("Enter the value");
                    int x3 = scanner.nextInt();
                    l.insertAtPos(x3);
                    l.display();
                    break;

                case 4:
                    l.del();
                    l.display();
                    break;

                case 5:
                    l.searchPos();
                    l.display();
                    break;

                case 6:
                    l.display();
                    break;

                case 7:
                    l.sort();
                    l.display();
                    break;

                case 8:
                    l.rev();
                    l.display();
                    break;

                case 9:
                    System.out.println("Exiting program.");
                    scanner.close(); 
                    System.exit(0);
                    break;

                default:
                    System.out.println("Wrong choice");
            }
        }
    }
}
