from bp_approx import read_instance
from bp_exact import solve


def main():
    C, w = read_instance()
    print(len(solve(C, w)))


if __name__ == "__main__":
    main()
