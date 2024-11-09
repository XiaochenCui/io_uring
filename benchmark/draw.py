import json

from matplotlib import pyplot as plt

import xiaochen_py


def draw():
    report_path = xiaochen_py.get_latest_report("./docs/record")

    # parse the json to list(BenchmarkRecord)
    f = open(report_path, "r")
    all_records = json.load(f, object_hook=lambda x: xiaochen_py.json_loader(**x))

    # get all the unique message_length
    message_length_list = set(
        r.target_attributes["message_length"] for r in all_records
    )

    client_number_list = list(
        set(r.target_attributes["client_number"] for r in all_records)
    )
    client_number_list.sort()

    target_list = set(r.target_attributes["target"] for r in all_records)

    points_list = []
    for message_length in message_length_list:
        for target in target_list:
            # filter the records by message_length and target
            records = list(
                filter(
                    lambda x: x.target_attributes["message_length"] == message_length
                    and x.target_attributes["target"] == target,
                    all_records,
                )
            )

            rps_list = [r.test_result["request_per_second"] for r in records]

            # draw points
            points = plt.scatter(client_number_list, rps_list, label=f"{target}")

            # draw lines
            plt.plot(client_number_list, rps_list)
            points_list.append(points)

        plt.xlabel("Concurrent Clients")
        plt.ylabel("Requests/Second")

        top = max([r.test_result["request_per_second"] for r in all_records]) * 1.3
        plt.ylim(bottom=0, top=top)

        plt.legend(handles=points_list, loc="upper right")

        plt.subplots_adjust(bottom=0.15)

        # Add text at the bottom
        plt.figtext(
            0.5,
            0.01,
            f"message length: {message_length} bytes, duration: 20s",
            ha="center",
            fontsize=10,
        )

        plt.savefig(
            f"./docs/img/echo_server_message_lenght_{message_length}_{xiaochen_py.timestamp()}.png"
        )


if __name__ == "__main__":
    draw()
