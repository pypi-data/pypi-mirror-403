package demo;

import java.util.Stack;

public class Postfix {
	public static int evaluatePostfix(String expr) {
        Stack<Integer> stack = new Stack<>();
        for (int i = 0; i < expr.length(); i++) {
            char ch = expr.charAt(i);
            if (Character.isDigit(ch)) {
                stack.push(ch - '0');
            } else {
                int b = stack.pop();
                int a = stack.pop();
                switch (ch) {
                    case '+':
                        stack.push(a + b);
                        break;
                    case '-':
                        stack.push(a - b);
                        break;
                    case '*':
                        stack.push(a * b);
                        break;
                    case '/':
                        if (b != 0) {
                            stack.push(a / b);
                        } else {
                            System.out.println("Division by zero error");
                            return -1;
                        }
                        break;
                    default:
                        System.out.println("Invalid operator: " + ch);
                        return -1;
                }
            }
        }
        return stack.pop();
    }

    public static void main(String[] args) {
        java.util.Scanner scanner = new java.util.Scanner(System.in);
        System.out.print("Enter Postfix Expression: ");
        String expr = scanner.next();
        int result = evaluatePostfix(expr);
        if (result != -1) {
            System.out.println("Result: " + result);
        }
        scanner.close();
    }
}
