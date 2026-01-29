package demo;
import java.util.*;

class GraphDFS {
    private Map<Integer, List<Integer>> adj;

    public GraphDFS() {
        adj = new HashMap<>();
    }

    public void addEdge(int v, int w) {
        adj.putIfAbsent(v, new ArrayList<>());
        adj.get(v).add(w);
    }

    public void DFS(int v, Set<Integer> visited) {
        visited.add(v);
        System.out.print(v + " ");
        for (int neighbor : adj.getOrDefault(v, new ArrayList<>())) {
            if (!visited.contains(neighbor)) {
                DFS(neighbor, visited);
            }
        }
    }

    public static void main(String[] args) {

        GraphDFS g = new GraphDFS();
        g.addEdge(0, 1);
        g.addEdge(0, 2);
        g.addEdge(1, 2);
        g.addEdge(2, 0);
        g.addEdge(2, 3);
        g.addEdge(3, 3);

        Set<Integer> visited = new HashSet<>();

        System.out.println("Following is Depth First Traversal (starting from vertex 2):");
        g.DFS(2, visited);
    }
}
