package demo;
import java.util.*;

public class GraphBFS {
    static final int NODE = 6;
    static int[][] graph = {
        {0, 1, 0, 1, 0, 0},
        {1, 0, 1, 0, 1, 0},
        {0, 1, 0, 1, 0, 1},
        {1, 0, 1, 0, 1, 0},
        {0, 1, 0, 1, 0, 1},
        {0, 0, 1, 0, 1, 0}
    };

    static class Node {
        int val;
        int state;
        public Node(int val) {
            this.val = val;
            this.state = 0;
        }
    }

    public static void bfs(Node[] vertices, Node start) {
        Node u;
        LinkedList<Node> queue = new LinkedList<>();
        for (int i = 0; i < NODE; i++) vertices[i].state = 0;

        vertices[start.val].state = 1;
        queue.add(start);

        while (!queue.isEmpty()) {
            u = queue.poll();
            System.out.print((char)(u.val + 'A') + " ");
            for (int i = 0; i < NODE; i++) {
                if (graph[u.val][i] == 1 && vertices[i].state == 0) {
                    vertices[i].state = 1;
                    queue.add(vertices[i]);
                }
            }
            u.state = 2;
        }
    }

    public static void main(String[] args) {
        System.out.println("Graph Traversal using BFS.\n");

        Node[] vertices = new Node[NODE];
        for (int i = 0; i < NODE; i++) vertices[i] = new Node(i);

        char s = 'C'; // Starting BFS from node 'C' (different)
        Node start = vertices[s - 'A'];

        System.out.print("BFS Traversal: ");
        bfs(vertices, start);
        System.out.println();
    }
}
