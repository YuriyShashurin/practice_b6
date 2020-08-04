from bottle import route
from bottle import run
import sqlalchemy as sql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from bottle import HTTPError
from bottle import request

DB_PATH = "sqlite:///albums.sqlite3"
Base = declarative_base()


class DuplicateAlbum(Exception):
    """
    создаем пользовательское исключение на наличие дубликата альбома
    """
    pass


class Album(Base):
    """
    Создаем структуру базы Album
    """

    __tablename__ = "album"

    id = sql.Column(sql.Integer, primary_key=True)
    year = sql.Column(sql.Integer)
    artist = sql.Column(sql.Text)
    genre = sql.Column(sql.Text)
    album = sql.Column(sql.Text)


def connect_db():
    """
    Соединение с базой
    """

    engine = sql.create_engine(DB_PATH)
    Base.metadata.create_all(engine)
    session = sessionmaker(engine)
    return session()


def validate_enter(year, artist, genre, album):
    """
        функция проверки данных из запроса на соответсвие типов
    """
    if type(year) == int and type(artist) == str and type(genre) == str and type(album) == str:
        result = True
    else:
        result = False
    return result


@route("/albums/<artist>")
# Выводим альбомы исполнителя по данным из GET запроса
def show_album(artist):
    # Подключаем базу
    session = connect_db()
    # Записываем информацию по заданному исполнителю из базы
    artist_item = session.query(Album).filter(Album.artist == artist).all()
    # Если информация есть, то готовим информацию по альбомам к выводу
    if artist_item:
        # Создаем пустой список
        artist_album = []
        for album in artist_item:
            # в список добавляем информацию по каждой записи с переносом строки
            artist_album += "Альбом исполнителя {}: {} {} года <br>".format(album.artist, album.album, album.year)
        # Возвращаем результ
        return artist_album
    # Если информации по исполнителю в базе нет, возвращаем соотвествующее предупреждение
    else:
        return "Данный исполнитель не найден"


@route("/albums", method="POST")
def add_artist():

    # добавляем данные из запрос в словарь
    user_enter = {
        "year": request.forms.get("year"),
        "artist": request.forms.get("artist"),
        "genre": request.forms.get("genre"),
        "album": request.forms.get("album")
    }
    # добавляем из словаря значения в переменные
    year = user_enter['year']
    artist = user_enter['artist']
    genre = user_enter['genre']
    album = user_enter['album']
    # проверяем является ли год числом
    try:
        year = int(year)
    except ValueError:

        return HTTPError(400, "Указан некорректный год альбома")
    # подключаемся
    session = connect_db()
    # мэтчим наличие данных по переданным в запросе данным
    check_album = session.query(Album).filter(Album.year == year, Album.artist == artist, Album.genre == genre, Album.album == album).first()
    # производим проверку данных из запроса на соответсвие типов
    check_enter = validate_enter(year, artist, genre, album)
    # Если возвращается True выполняем попытку сохранить данные
    if check_enter:
        try:
            # Если запись с такими же данными уже существует, то возвращаем пользовательское исключение
            if check_album is not None:
                raise DuplicateAlbum("данный альбом уже добавлен в базу")
            # В ином случае сохраняем данные в базу
            new_album = Album(

                year=year,
                artist=artist,
                genre=genre,
                album=album,

            )
            session.add(new_album)
            session.commit()
            # Возвращаем сообщение об успешном добавлении
            return "Альбом {} {} года в жанре {} артиста {} добавлен".format(new_album.album, new_album.year, new_album.genre, new_album.artist)
        # Если сработало исключение, перехватываем его
        except DuplicateAlbum as err:
            return HTTPError(409, str(err))
    # Если проверка типов вернула False выводим соответствующее сообщение
    else:
        return "Неправильно введены данные"

# Запускаем сервер


if __name__ == "__main__":
    run(host="localhost", port=8082, debug=True)

