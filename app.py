
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

from genetic_algorithm import genetic_algorithm

# Page configuration
st.set_page_config(
    page_title="TV Scheduling Using Genetic Algorithm",
    page_icon="📺",
    layout="wide"
)

st.title("📺 TV Scheduling Using Genetic Algorithm")

st.write(
    "This application generates an optimized TV program "
    "schedule using a Genetic Algorithm."
)

# --------------------------------------------------
# 1. GENETIC ALGORITHM PARAMETERS
# --------------------------------------------------

st.header("Genetic Algorithm Parameters")

col1, col2 = st.columns(2)

with col1:
    crossover_rate = st.slider(
        "Crossover Rate (CO_R)",
        min_value=0.00,
        max_value=0.95,
        value=0.80,
        step=0.01
    )

with col2:
    mutation_mode = st.radio(
        "Mutation Mode",
        [
            "Default (0.20)",
            "Custom (0.01 to 0.05)"
        ]
    )

    if mutation_mode == "Default (0.20)":
        mutation_rate = 0.20
        st.info(
            "Using lecturer's default mutation rate: 0.20"
        )
    else:
        mutation_rate = st.slider(
            "Mutation Rate (MUT_R)",
            min_value=0.01,
            max_value=0.05,
            value=0.02,
            step=0.01
        )

# Display current parameters
st.subheader("Current Parameters")

st.write("**Crossover Rate:**", crossover_rate)
st.write("**Mutation Rate:**", mutation_rate)
st.write("**Generations:** 100")
st.write("**Population Size:** 50")
st.write("**Elitism Size:** 2")

st.divider()

# Dataset location
CSV_PATH = (
    Path(__file__).resolve().parent
    / "program_ratings_modified.csv"
)

# --------------------------------------------------
# 2. GENERATE TV SCHEDULE
# --------------------------------------------------

if st.button("Generate TV Schedule", type="primary"):

    if not CSV_PATH.exists():
        st.error("Modified CSV file not found.")

    else:
        with st.spinner("Running Genetic Algorithm..."):

            best_schedule, fitness_history, ratings = genetic_algorithm(
                file_path=str(CSV_PATH),
                generations=100,
                population_size=50,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                elitism_size=2,
                seed=42
            )

            # Prepare schedule data
            schedule_data = []

            for index, program in enumerate(best_schedule):
                schedule_data.append({
                    "Time Slot": f"{index + 6:02d}:00",
                    "Program": program,
                    "Rating": ratings[program][index]
                })

            schedule_df = pd.DataFrame(schedule_data)

        st.success("TV Schedule Generated Successfully!")

        # --------------------------------------------------
        # 3. FITNESS RESULTS
        # --------------------------------------------------

        st.header("Genetic Algorithm Results")

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Initial Best Fitness",
            f"{fitness_history[0]:.2f}"
        )

        metric2.metric(
            "Final Best Fitness",
            f"{fitness_history[-1]:.2f}"
        )

        metric3.metric(
            "Fitness Improvement",
            f"{fitness_history[-1] - fitness_history[0]:.2f}"
        )

        # --------------------------------------------------
        # 4. DISPLAY TV SCHEDULE
        # --------------------------------------------------

        st.header("Optimized TV Schedule")

        st.dataframe(
            schedule_df,
            width="stretch",
            hide_index=True
        )

        # --------------------------------------------------
        # 5. FITNESS PROGRESS CHART
        # --------------------------------------------------

        st.header("Fitness Progress Across Generations")

        fitness_df = pd.DataFrame({
            "Generation": range(len(fitness_history)),
            "Best Fitness": fitness_history
        })

        min_fitness = max(
            0,
            min(fitness_history) - 0.5
        )

        max_fitness = max(fitness_history) + 0.5
        last_generation = len(fitness_history) - 1

        fitness_chart = (
            alt.Chart(fitness_df)
            .mark_line(point=True, strokeWidth=2)
            .encode(
                x=alt.X(
                    "Generation:Q",
                    title="Generation",
                    scale=alt.Scale(
                        domain=[0, last_generation],
                        nice=False
                    ),
                    axis=alt.Axis(
                        values=[0, 20, 40, 60, 80, 100]
                    )
                ),
                y=alt.Y(
                    "Best Fitness:Q",
                    title="Best Fitness Score",
                    scale=alt.Scale(
                        domain=[min_fitness, max_fitness],
                        zero=False,
                        nice=False
                    )
                ),
                tooltip=[
                    alt.Tooltip(
                        "Generation:Q",
                        title="Generation"
                    ),
                    alt.Tooltip(
                        "Best Fitness:Q",
                        title="Fitness",
                        format=".2f"
                    )
                ]
            )
            .properties(height=350)
        )

        st.altair_chart(
            fitness_chart,
            width="stretch"
        )

        # --------------------------------------------------
        # 6. SCHEDULE VALIDATION
        # --------------------------------------------------

        st.subheader("Schedule Validation")

        st.write(
            "Total Time Slots:",
            len(best_schedule)
        )

        st.write(
            "Unique Programs:",
            len(set(best_schedule))
        )

        if (
            len(best_schedule) == 18
            and len(set(best_schedule)) == 10
        ):
            st.success("Schedule Validation: PASSED")
        else:
            st.error("Schedule Validation: FAILED")

        # --------------------------------------------------
        # 7. DOWNLOAD SCHEDULE
        # --------------------------------------------------

        st.download_button(
            "Download Schedule CSV",
            data=schedule_df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="generated_tv_schedule.csv",
            mime="text/csv"
        )
