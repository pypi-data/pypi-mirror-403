package demo;

import java.util.Scanner;

public class BST {

    // Node structure for the tree
    class BSTNode {
        int data;
        BSTNode left, right;

        public BSTNode(int item) {
            data = item;
            left = right = null;
        }
    }

    private BSTNode tree;

    public BST() {
        tree = null;
    }

    // Method to insert nodes in BST
    public BSTNode createTree(BSTNode node, int item) {
        if (node == null) {
            node = new BSTNode(item);
        } else {
            if (item < node.data) {
                node.left = createTree(node.left, item);
            } else {
                node.right = createTree(node.right, item);
            }
        }
        return node;
    }

    // Preorder traversal
    public void preorder(BSTNode node) {

        if (node != null) {
            System.out.print(" " + node.data);
            preorder(node.left);
            preorder(node.right);
        }
    }

    // Inorder traversal
    public void inorder(BSTNode node) {
        if (node != null) {
            inorder(node.left);
            System.out.print(" " + node.data);
            inorder(node.right);
        }
    }

    // Postorder traversal
    public void postorder(BSTNode node) {
        if (node != null) {
            postorder(node.left);
            postorder(node.right);
            System.out.print(" " + node.data);
        }
    }

    // Count total nodes
    public int totalNodes(BSTNode node) {
        if (node == null) {
            return 0;
        }
        return totalNodes(node.left) + totalNodes(node.right) + 1;
    }

    // Find smallest node
    public void findSmallestNode(BSTNode node) {
        if (node == null) {
            System.out.println("Tree is empty");
            return;
        }
        while (node.left != null) {
            node = node.left;
        }
        System.out.println(node.data);
    }

    // Find largest node
    public void findLargestNode(BSTNode node) {
        if (node == null) {
            System.out.println("Tree is empty");
            return;
        }
        while (node.right != null) {
            node = node.right;
        }
        System.out.println(node.data);
    }

    // Main method
    public static void main(String[] args) {

        BST obj = new BST();
        Scanner scanner = new Scanner(System.in);
        int choice, n, item;

        while (true) {
            System.out.println("\nBinary Search Tree Operations");
            System.out.println("1) Create Tree");
            System.out.println("2) Traversal");
            System.out.println("3) Total Nodes");
            System.out.println("4) Insert Node");
            System.out.println("5) Find Smallest Node");
            System.out.println("6) Find Largest Node");
            System.out.println("7) Exit");
            System.out.print("Enter your choice: ");
            choice = scanner.nextInt();

            switch (choice) {

                case 1:
                    System.out.print("\nHow many nodes do you want to enter? ");
                    n = scanner.nextInt();
                    for (int i = 0; i < n; i++) {
                        System.out.print("Enter value: ");
                        item = scanner.nextInt();
                        obj.tree = obj.createTree(obj.tree, item);
                    }
                    break;

                case 2:
                    System.out.println("\nInorder:");
                    obj.inorder(obj.tree);
                    System.out.println("\nPreorder:");
                    obj.preorder(obj.tree);
                    System.out.println("\nPostorder:");
                    obj.postorder(obj.tree);
                    break;

                case 3:
                    System.out.println("Total nodes: " + obj.totalNodes(obj.tree));
                    break;

                case 4:
                    System.out.print("Enter value to insert: ");
                    item = scanner.nextInt();
                    obj.tree = obj.createTree(obj.tree, item);
                    System.out.println("Node inserted.");
                    break;

                case 5:
                    System.out.print("Smallest node: ");
                    obj.findSmallestNode(obj.tree);
                    break;

                case 6:
                    System.out.print("Largest node: ");
                    obj.findLargestNode(obj.tree);
                    break;

                case 7:
                    System.out.println("Exiting...");
                    scanner.close();
                    System.exit(0);

                default:
                    System.out.println("Invalid choice. Try again.");
            }
        }
    }
}
