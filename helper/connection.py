import mysql.connector

# Creating connection object
sql_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=""
)

# query = "SELECT a.ArtistId, a.Name as Artist_Name, a2.AlbumId, a2.Title, t.TrackId, t.Name, t.UnitPrice, t.Bytes, g.GenreId, g.Name FROM Chinook.Artist a left join Chinook.Album a2 on a2.ArtistId = a.ArtistId LEFT join Chinook.Track t on t.AlbumId = a2.AlbumId join Chinook.Genre g on g.GenreId = t.GenreId ORDER by a.ArtistId ASC "



def ReadData (query):
    cursor = sql_db.cursor()
    cursor.execute(query)
    records = cursor.fetchall()
    sql_db.close()
    cursor.close()
    return records
    
