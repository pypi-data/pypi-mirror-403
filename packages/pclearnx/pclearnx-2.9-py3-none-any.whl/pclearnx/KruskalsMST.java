package demo;
import java.util.*;

public class KruskalsMST {
    static int[] father;
    static edge[] tree;
    static int wt_tree = 0;
    static int cnt = 0;
    static int n;

    static class edge {
        int u, v, weight;
    }

    public static int find(int i) {
        if (father[i] < 0) return i;
        father[i] = find(father[i]);
        return father[i];
    }

    public static void union(int root1, int root2) {
        if (father[root1] < father[root2]) {
            father[root1] += father[root2];
            father[root2] = root1;
        } else {
            father[root2] += father[root1];
            father[root1] = root2;
        }
    }

    public static void insert_tree(int i, int j, int wt) {
        cnt++;
        tree[cnt] = new edge();
        tree[cnt].u = i;
        tree[cnt].v = j;
        tree[cnt].weight = wt;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.print("Enter the number of nodes: ");
        n = sc.nextInt();
        father = new int[n + 1];
        Arrays.fill(father, -1);
        tree = new edge[n];

        List<edge> edges = new ArrayList<>();
        int origin, destin, wt;

        System.out.println("Enter edges (0 0 to quit) weight: ");
        while (true) {
            System.out.print("Enter origin and destination (0 0 to quit): ");
            origin = sc.nextInt();
            destin = sc.nextInt();
            if (origin == 0 && destin == 0) break;

            System.out.print("Enter weight for this edge: ");
            wt = sc.nextInt();

            if (origin > n || destin > n || origin <= 0 || destin <= 0) {
                System.out.println("Invalid edge");
                continue;
            }

            edge e = new edge();
            e.u = origin;
            e.v = destin;
            e.weight = wt;
            edges.add(e);
        }

        if (edges.size() < n - 1) {
            System.out.println("Spanning tree is not possible.");
            sc.close();
            return;
        }

        Collections.sort(edges, new Comparator<edge>() {
            public int compare(edge e1, edge e2) {
                return e1.weight - e2.weight;
            }
        });

        // Kruskal's algorithm
        for (int i = 0; i < edges.size() && cnt < n - 1; i++) {
            edge tmp = edges.get(i);
            int root1 = find(tmp.u);
            int root2 = find(tmp.v);
            if (root1 != root2) {
                insert_tree(tmp.u, tmp.v, tmp.weight);
                wt_tree += tmp.weight;
                union(root1, root2);
            }
        }

        System.out.println("\nEdges to be included in spanning tree:");
        for (int i = 1; i <= cnt; i++) {
            System.out.println(tree[i].u + " - " + tree[i].v + " (Weight: " + tree[i].weight + ")");
        }
        System.out.println("Weight of this spanning tree is: " + wt_tree);
        sc.close();
    }
}
