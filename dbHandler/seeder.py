from dbHandler import Base, engine, Session


def regenerate_tables():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return


def seed_elements(num_elements: int = 150):
    from dbHandler import Element
    from random import uniform, choice

    session = Session()

    # create elements
    status_choices = [0, 1, 2, 3, 4, 5, 15]
    for i in range(num_elements):
        description = "Seeded Element no. {}".format(i)
        latitude = uniform(0, 180)
        longitude = uniform(0, 180)
        status = choice(status_choices)
        element = Element(description, latitude, longitude, status)
        session.add(element)

    # commit and close
    session.commit()
    session.close()
    return


if __name__ == "__main__":
    regenerate_tables()
    seed_elements()
