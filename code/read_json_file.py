import json
import asyncio


async def main():
    with open("user_info.json", 'r') as f:
        data = json.load(f)

    print("PRINTING DATA NICELY")

    for i in data["user"]:
        print(i, ": ")

        if type(data["user"][i]) == dict:
            for j in data["user"][i]:
                print("\t", j, ": ", data["user"][i][j])
        else:
            print("\t", data["user"][i])


if __name__ == "__main__":
    asyncio.run(main())
