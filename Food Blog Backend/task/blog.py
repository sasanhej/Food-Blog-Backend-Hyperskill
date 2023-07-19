import sqlite3
import sys


args = sys.argv
#dbname = args[1]
dbname = 'food_blog.db'


conn = sqlite3.connect(dbname)
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS meals(
meal_id INTEGER PRIMARY KEY,
meal_name TEXT NOT NULL UNIQUE
);
''')
conn.commit()
cur.execute('''
CREATE TABLE IF NOT EXISTS ingredients(
ingredient_id INTEGER PRIMARY KEY,
ingredient_name  TEXT NOT NULL UNIQUE
);
''')
conn.commit()
cur.execute('''
CREATE TABLE IF NOT EXISTS measures(
measure_id INTEGER PRIMARY KEY,
measure_name TEXT UNIQUE
);
''')
conn.commit()
cur.execute('''
CREATE TABLE IF NOT EXISTS recipes(
recipe_id INTEGER PRIMARY KEY,
recipe_name TEXT NOT NULL,
recipe_description TEXT
);
''')
conn.commit()


# Stage 1/5
data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
        "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
        "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}

for j in data:
    for i in data[j]:
        cur.execute(f'INSERT INTO {j} ({j[:-1]}_name) VALUES ("{i}");')
        conn.commit()

# Stage 2/5
print('Pass the empty recipe name to exit.')
while True:
    recipe_name = input('Recipe name:')
    if recipe_name == "":
        break
    recipe_description = input('Recipe description:')
    cur.execute(f'INSERT INTO recipes(recipe_name, recipe_description) VALUES (?,?);',
                (recipe_name, recipe_description))
    conn.commit()
conn.close()