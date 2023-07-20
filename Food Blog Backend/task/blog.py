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

cur.execute('''PRAGMA foreign_keys = ON;''')
conn.commit()

cur.execute('''
CREATE TABLE IF NOT EXISTS serve(
serve_id INTEGER PRIMARY KEY,
recipe_id INTEGER NOT NULL,
meal_id INTEGER NOT NULL,
FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
FOREIGN KEY(meal_id) REFERENCES meals(meal_id)
);
''')
conn.commit()

cur.execute('''
CREATE TABLE IF NOT EXISTS quantity(
quantity_id INTEGER PRIMARY KEY,
quantity INTEGER NOT NULL,
recipe_id INTEGER NOT NULL,
measure_id INTEGER NOT NULL,
ingredient_id INTEGER NOT NULL,
FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
FOREIGN KEY(measure_id) REFERENCES measures(measure_id),
FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id)
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
    # Srage 3/5
    cur.execute('SELECT meal_id, meal_name FROM meals;')
    meals = input("".join([f'{meal[0]}) {meal[1]} ' for meal in cur.fetchall()])+'\nEnter proposed meals separated by a space: ').split(' ')
    recipe_id = cur.execute('INSERT INTO recipes(recipe_name, recipe_description) VALUES (?,?);', (recipe_name, recipe_description)).lastrowid
    conn.commit()
    for j in meals:
        cur.execute('INSERT INTO serve(meal_id, recipe_id) VALUES (?,?);', (int(j), int(recipe_id)))
        conn.commit()
    # Stage 4/5
    while True:
        ingredients = input('Input quantity of ingredient <press enter to stop>:')
        if ingredients == "":
            break
        ingredients = ingredients.split(" ")
        quantity = ingredients[0]
        if len(ingredients) == 3:
            measure_name = ingredients[1]
            ingredient_name = ingredients[2]
            cur.execute(f'SELECT measure_id FROM measures WHERE measure_name LIKE "{measure_name}%";')
            measure_list = cur.fetchall()
            if len(measure_list) != 1:
                continue
        else:
            ingredient_name = ingredients[1]
            cur.execute('SELECT measure_id FROM measures WHERE measure_name="";')
            measure_id = cur.fetchall()
        measure_id = measure_list[0][0]
        cur.execute(f'SELECT ingredient_id FROM ingredients WHERE ingredient_name LIKE "%{ingredient_name}%";')
        ingredient_list = cur.fetchall()
        if len(ingredient_list) != 1:
            continue
        ingredient_id = ingredient_list[0][0]
        cur.execute('INSERT INTO quantity(quantity, recipe_id, measure_id, ingredient_id) VALUES (?,?,?,?);', (quantity, recipe_id, measure_id, ingredient_id))
        conn.commit()

conn.close()
# Stage 5/5