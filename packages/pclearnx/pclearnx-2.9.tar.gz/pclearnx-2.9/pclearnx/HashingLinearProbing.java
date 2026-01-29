package demo;

import java.util.Arrays;

public class HashingLinearProbing {
	private static final int TABLE_SIZE = 10;
    private Integer[] table;

    public HashingLinearProbing() {
        table = new Integer[TABLE_SIZE];
        Arrays.fill(table, null);
    }

    private int moduloHash(int key) {
        return Math.abs(key) % TABLE_SIZE;
    }

    private int digitExtractionHash(int key) {
        String keyStr = String.valueOf(Math.abs(key));
        if (keyStr.length() < 4) {
            return moduloHash(key);
        }

        int digit2 = Character.getNumericValue(keyStr.charAt(1));
        int digit3 = Character.getNumericValue(keyStr.charAt(2));
        int extractedVal = digit2 * 10 + digit3;

        return Math.abs(extractedVal) % TABLE_SIZE;
    }

    public void insert(int key, boolean useDigitExtraction) {
        int index = useDigitExtraction ? digitExtractionHash(key) : moduloHash(key);
        int startIndex = index;

        while (table[index] != null) {
            if (table[index].equals(key)) {
                return;
            }
            index = (index + 1) % TABLE_SIZE;
            if (index == startIndex) {
                System.out.println("Error: Hash table is full. Cannot insert key " + key);
                return;
            }
        }

        table[index] = key;
        System.out.println("Inserted Key " + key + " at index " + index);
    }

    public void printTable() {
        System.out.println("\nHash Table Contents:");
        for (int i = 0; i < TABLE_SIZE; i++) {
            System.out.println("Index " + i + ": " + (table[i] == null ? "Empty" : table[i]));
        }
    }

    public static void main(String[] args) {
    	HashingLinearProbing ht = new HashingLinearProbing();
        System.out.println("sahabuddin 91");
        System.out.println("--- Using Modulo Division Hashing ---");

        int[] keys = {42, 63, 74, 81, 96, 107};
        for (int key : keys) {
            ht.insert(key, false);
        }
        ht.printTable();

        HashingLinearProbing ht2 = new HashingLinearProbing();
        System.out.println("\n--- Using Digit Extraction Hashing ---");

        ht2.insert(2468, true);
        ht2.insert(7391, true);
        ht2.insert(5084, true);
        ht2.insert(2222, true);
        ht2.printTable();
    }
}
