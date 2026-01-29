package demo;
import java.util.Scanner;

class BracketNode {
    int data;
    BracketNode next;
}

public class parenthesis {
    static BracketNode top = null;

    static void push(char x) {
        BracketNode tmp = new BracketNode();
        tmp.data = x;
        tmp.next = null;
        if (top == null) {
            top = tmp;
        } else {
            BracketNode tmp1 = top;
            top = tmp;
            tmp.next = tmp1;
        }
    }

    static char pop() {
        if (top == null) {
            System.out.println("Stack is empty.");
            return '\0';
        } else {
            BracketNode ptr = top;
            top = top.next;
            char data = (char) ptr.data;
            return data;
        }
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int len;
        char c, d, e;
        char[] a = new char[30];

        System.out.println("Enter expression :");
        String input = scanner.nextLine();
        len = input.length();
        a = input.toCharArray();

        for (int i = 0; i < len; i++) {
            if (a[i] == '{' || a[i] == '[' || a[i] == '(') {
                push(a[i]);
            } else {
                switch (a[i]) {
                    case ')':
                        c = pop();
                        if (c == '{' || c == '[') {
                            System.out.println("Invalid");
                            return;
                        }
                        break;
                    case ']':
                        d = pop();
                        if (d == '{' || d == '(') {
                            System.out.println("Invalid");
                            return;
                        }
                        break;
                    case '}':
                        e = pop();
                        if (e == '(' || e == '[') {
                            System.out.println("Invalid");
                            return;
                        }
                        break;
                    default:
                        System.out.println("Enter the correct choice");
                        return;
                }
            }
        }

        if (top == null)
            System.out.println("Balanced");
        else
            System.out.println("Unbalanced");

        scanner.close();
    }
}
