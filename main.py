import clinic

def main():

    sim = clinic.ClinicSimulation()
    params = sim.get_default_params()
    sim.run(params)
    print sim.get_json()

if __name__ == "__main__":
    main()
