from hashlib import sha224

from sqlalchemy.orm import sessionmaker

from dbHandler import Base, engine


def regenerate_tables():
    """
    Wipes out all data in DB and recreates the tables.

    :return:
    """

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return


def seed_lighting_components():
    """
    A very ugly seeder that allows for no customizability.... Yet....

    TODO #7: Make function more flexible. Low priority.

    :return:
    """

    from dbHandler import Element, Telecell, Asset, Basestation
    from random import uniform, choice

    session = sessionmaker(bind=engine)()

    status_choices = [0, 1, 2, 15]
    bs_version_choices = [3, 4]
    basestations = []
    telecell_uuid = 1

    # create 5 Basestations
    for i in range(5):
        lat, long = uniform(-180, 180), uniform(-180, 180)
        bs = Basestation(i + 1, choice(bs_version_choices), lat, long)
        basestations.append(bs)
        session.add(bs)

    # 1 element unassociated to a telecell, and 1 asset associated to 1 element.
    description = "1 element unassociated to a telecell, and 1 asset associated to 1 element"
    for i in range(99):
        lat, long = uniform(-180, 180), uniform(-180, 180)
        asset = Asset(latitude=lat, longitude=long)
        element = Element(asset=asset, description="{} {}".format(description, i), status=choice(status_choices))
        session.add(asset)
        session.add(element)

    # 1 element associated to 1 telecell, and 1 asset associated to 1 element.
    description = "1 element associated to 1 telecell, and 1 asset associated to 1 element"
    for i in range(209):
        lat, long = uniform(-180, 180), uniform(-180, 180)
        asset = Asset(latitude=lat, longitude=long)
        telecell = Telecell(telecell_uuid, False, lat, long, choice(basestations))
        telecell_uuid += 1
        element = Element(asset=asset, description="{} {}".format(description, i),
                          status=choice(status_choices), telecell=telecell)
        session.add(asset)
        session.add(element)

    # 1 element associated to 1 telecell, and 1 asset associated to 2 elements.
    description = "1 element associated to 1 telecell, and 1 asset associated to 2 elements"
    for i in range(119):
        lat, long = uniform(-180, 180), uniform(-180, 180)
        asset = Asset(latitude=lat, longitude=long)
        telecell_1 = Telecell(telecell_uuid, False, lat, long, choice(basestations))
        telecell_uuid += 1
        telecell_2 = Telecell(telecell_uuid, False, lat, long, choice(basestations))
        telecell_uuid += 1
        element_1 = Element(asset=asset, description="{} {}".format(description, i),
                            status=choice(status_choices), telecell=telecell_1)
        element_2 = Element(asset=asset, description="{} {}".format(description, i),
                            status=choice(status_choices), telecell=telecell_2)
        session.add(asset)
        session.add(telecell_1)
        session.add(element_1)
        session.add(telecell_2)
        session.add(element_2)

    # 2 elements associated to 1 telecell, and 1 asset associated to 1 element.
    description = "2 elements associated to 1 telecell, and 1 asset associated to 1 element."
    for i in range(129):
        lat, long = uniform(-180, 180), uniform(-180, 180)
        asset = Asset(latitude=lat, longitude=long)
        telecell = Telecell(telecell_uuid, False, lat, long, choice(basestations))
        telecell_uuid += 1
        element_1 = Element(asset=asset, description="{} {}".format(description, i),
                            status=choice(status_choices), telecell=telecell)
        element_2 = Element(asset=asset, description="{} {}".format(description, i),
                            status=choice(status_choices), telecell=telecell)
        session.add(asset)
        session.add(telecell)
        session.add(element_2)
        session.add(element_1)

    session.commit()
    session.close()

    return


def seed_users(n):
    from dbHandler import User
    from random import randint, choice
    session = sessionmaker(bind=engine)()
    roles = [i for i in range(2, 9, 2)]

    for i in range(n):
        username = "telensa-{}".format(str(randint(0, 100000)))
        hashed = sha224("1ns3cure".encode('utf-8')).hexdigest()
        user = User(username, hashed, choice(roles))
        session.add(user)

    session.commit()
    session.close()


if __name__ == "__main__":
    regenerate_tables()
    seed_users(10)
    seed_lighting_components()
