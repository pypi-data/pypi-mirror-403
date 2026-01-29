package demo; 

public class PolynomialAddition { 

    public static int max(int m, int n) { 
        return (m > n) ? m : n; 
    } 

    public static int[] add(int[] A, int[] B, int m, int n) { 
        int size = max(m, n); 
        int[] sum = new int[size]; 

        for (int i = 0; i < m; i++) { 
            sum[i] = A[i]; 
        } 
        for (int i = 0; i < n; i++) { 
            sum[i] += B[i]; 
        } 
        return sum; 
    } 

    public static void printPoly(int[] poly, int n) { 
        for (int i = 0; i < n; i++) { 
            System.out.print(poly[i]); 
            if (i != 0) { 
                System.out.print("x^" + i); 
            } 
            if (i != n - 1) { 
                System.out.print(" + "); 
            } 
        } 
        System.out.println(); 
    } 

    public static void main(String[] args) { 

        System.out.println("\nPOLYNOMIAL ADDITION\n"); 

        int[] A = { 1, 0, 2, 4 }; 
        int[] B = { 3, 5, 7 }; 

        int m = A.length; 
        int n = B.length; 

        System.out.println("First polynomial is "); 
        printPoly(A, m); 

        System.out.println("Second polynomial is "); 
        printPoly(B, n); 

        int[] sum = add(A, B, m, n); 
        int size = max(m, n); 

        System.out.println("\nSum polynomial is "); 
        printPoly(sum, size); 
    } 
} 
