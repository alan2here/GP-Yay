import do

# TODO this file is not working or finished

class agent:
    def __init__(self) -> None:
        self.personality = do.random_personality()
        self.memories = []
        self.memories_location = []
        self.nearby = ""

    def location(self) -> str:
        return self.memories_location[-1]

    def periodically(self) -> None: # once per day
        # simplify memories
        for index in range(self.memories.__len__):
            self.memories[index] = do.simplify(self.memories[index])

    def opinion(self, of : str) -> str:
        return do.opinion(self.personality, of)

    # populate "nearby" and "location"
    def look(self, token_count : int):
        self.nearby = "" # this line needs to be replaced by the real code to do this

        # update memories_location if your location has changed
        old_location = str(self.location()) # hopefully this copies the string
        location = do.location_from_entities(token_count, self.nearby)
        if not do.same_meaning(old_location, location):
            self.memories_location.append(location)

    # ["book", "shelf", "book", "table"] --> "book, shelf, book, table"
    def entityList_to_str(entity_list : list) -> str:
        entities = entity_list[0]
        for entity in entity_list[1:]:
            entities += ", " + entity
        return entities
