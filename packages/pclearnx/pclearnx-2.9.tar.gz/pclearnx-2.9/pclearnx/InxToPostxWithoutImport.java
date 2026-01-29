package demo; 
import java.util.Scanner; 

public class InxToPostxWithoutImport { 
    static final int MAX = 100; 

    public static int precedence(char c) { 
        if (c == '^') return 3; 
        if (c == '*' || c == '/') return 2; 
        if (c == '+' || c == '-') return 1; 
        return -1; 
    } 

    public static boolean isOperand(char c) { 
        return Character.isLetterOrDigit(c); 
    } 

    public static String inxToPostx(String inx) { 
        char[] stack = new char[MAX]; 
        int top = -1; 
        StringBuilder postx = new StringBuilder(); 

        for (int i = 0; i < inx.length(); i++) { 
            char currentChar = inx.charAt(i); 

            if (isOperand(currentChar)) { 
                postx.append(currentChar); 
            } else if (currentChar == '(') { 
                stack[++top] = currentChar; 
            } else if (currentChar == ')') { 
                while (top != -1 && stack[top] != '(') { 
                    postx.append(stack[top--]); 
                } 
                top--; 
            } else { 
                while (top != -1 && precedence(stack[top]) >= precedence(currentChar)) { 
                    postx.append(stack[top--]); 
                } 
                stack[++top] = currentChar; 
            } 
        } 

        while (top != -1) { 
            postx.append(stack[top--]); 
        } 
        return postx.toString(); 
    } 

    public static void main(String[] args) { 
        Scanner scanner = new Scanner(System.in); 
        System.out.print("\nEnter the infix expression: ");
        String inx = scanner.nextLine(); 
        String postx = inxToPostx(inx); 
        System.out.println("Postfix Expression: " + postx); 
        scanner.close(); 
    } 
}
