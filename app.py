Replace the entire contents of `app.py` on GitHub with the code below, then click **Commit changes** and commit directly to `main`. Your Streamlit app should update automatically.

This version keeps the same algorithm settings and adds a clearer layout, improved typography, result cards, and a cleaner fitness chart. It also keeps the latest results visible when you adjust the sliders, while reminding you to generate a new schedule.

```python
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

from genetic_algorithm import genetic_algorithm


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="TV Scheduling Dashboard",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.025em;
        }

        h2 {
            margin-top: 0.4rem;
        }

        .hero {
            padding: 2rem 2.2rem;
            border-radius: 18px;
            background: linear-gradient(120deg, #183153, #254e77);
            color: #ffffff;
            margin-bottom: 1.8rem;
        }

        .hero-label {
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: #c4dcf4;
            margin-bottom: 0.65rem;
        }

        .hero-title {
            font-size: clamp(1.8rem, 3vw, 2.7rem);
            line-height: 1.15;
            font-weight: 750;
            margin-bottom: 0.65rem;
        }

        .hero-description {
            font-size: 1rem;
            line-height: 1.6;
            color: #e0ebf5;
            max-width: 760px;
        }

        div[data-testid="stMetric"] {
            padding: 1.2rem;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 12px;
            height: 100%;
        }

        div[data-testid="stMetricValue"] {
            font-weight: 700;
        }

        div.stButton > button {
            border-radius: 9px;
            font-weight: 600;
            min-height: 46px;
        }

        div.stDownloadButton > button {
            border-radius: 9px;
            font-weight: 600;
            min-height: 42px;
        }

        @media (max-width: 600px) {
            .hero {
                padding: 1.5rem;
            }

            .block-container {
                padding-top: 1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-label">Evolutionary Computing</div>
        <div class="hero-title">TV Scheduling Dashboard</div>
        <div class="hero-description">
            Explore how crossover and mutation rates affect a TV programme
            schedule generated using a genetic algorithm.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# PARAMETERS
# --------------------------------------------------

st.header("1. Set your parameters")
st.caption(
    "Choose the rates below, then generate a schedule to see the results."
)

with st.container(border=True):
    crossover_col, mutation_col = st.columns(2, gap="large")

    with crossover_col:
        st.subheader("Crossover")
        st.caption(
            "Controls how often two parent schedules are combined."
        )

        crossover_rate = st.slider(
            "Crossover rate (CO_R)",
            min_value=0.00,
            max_value=0.95,
            value=0.80,
            step=0.01,
            format="%.2f"
        )

    with mutation_col:
        st.subheader("Mutation")
        st.caption(
            "Controls how often an offspring schedule is changed."
        )

        mutation_mode = st.radio(
            "Mutation mode",
            options=[
                "Default (0.20)",
                "Custom (0.01 to 0.05)"
            ],
            horizontal=True
        )

        if mutation_mode == "Default (0.20)":
            mutation_rate = 0.20
            st.caption("The assignment specifies 0.20 as the default.")
        else:
            mutation_rate = st.slider(
                "Mutation rate (MUT_R)",
                min_value=0.01,
                max_value=0.05,
                value=0.02,
                step=0.01,
                format="%.2f"
            )

    st.divider()

    st.markdown("**Fixed experiment settings**")
    setting1, setting2, setting3, setting4 = st.columns(4)

    setting1.metric("Generations", "100")
    setting2.metric("Population", "50")
    setting3.metric("Elitism", "2")
    setting4.metric("Random seed", "42")

    st.write("")

    generate = st.button(
        "Generate TV schedule",
        type="primary",
        width="stretch"
    )

# --------------------------------------------------
# RUN THE GENETIC ALGORITHM
# --------------------------------------------------

CSV_PATH = (
    Path(__file__).resolve().parent
    / "program_ratings_modified.csv"
)

if generate:
    if not CSV_PATH.exists():
        st.error(
            "The modified ratings file was not found. "
            "Check that program_ratings_modified.csv is in the "
            "same GitHub folder as app.py."
        )
    else:
        try:
            with st.spinner("Generating your schedule..."):
                best_schedule, fitness_history, ratings = (
                    genetic_algorithm(
                        file_path=str(CSV_PATH),
                        generations=100,
                        population_size=50,
                        crossover_rate=crossover_rate,
                        mutation_rate=mutation_rate,
                        elitism_size=2,
                        seed=42
                    )
                )

                schedule_data = []

                for index, program in enumerate(best_schedule):
                    schedule_data.append({
                        "Time Slot": f"{index + 6:02d}:00",
                        "Program": program,
                        "Rating": ratings[program][index]
                    })

                schedule_df = pd.DataFrame(schedule_data)

                # Save the result so it stays visible when controls change.
                st.session_state["schedule_result"] = {
                    "schedule": best_schedule,
                    "schedule_df": schedule_df,
                    "fitness_history": fitness_history,
                    "programs": list(ratings.keys()),
                    "crossover_rate": crossover_rate,
                    "mutation_rate": mutation_rate
                }

        except Exception as error:
            st.error(f"Unable to generate the schedule: {error}")

# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

result = st.session_state.get("schedule_result")

if result is None:
    st.info(
        "Your results will appear here after you generate a schedule."
    )
else:
    schedule = result["schedule"]
    schedule_df = result["schedule_df"]
    fitness_history = result["fitness_history"]

    initial_fitness = fitness_history[0]
    final_fitness = fitness_history[-1]
    improvement = final_fitness - initial_fitness
    average_rating = final_fitness / len(schedule)

    st.write("")
    st.header("2. Review your results")

    st.caption(
        f"Results shown for CO_R = {result['crossover_rate']:.2f} "
        f"and MUT_R = {result['mutation_rate']:.2f}."
    )

    if (
        crossover_rate != result["crossover_rate"]
        or mutation_rate != result["mutation_rate"]
    ):
        st.info(
            "Your selected parameters have changed. "
            "Click Generate TV schedule to run them."
        )

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Initial best fitness",
        f"{initial_fitness:.2f}"
    )

    metric2.metric(
        "Final best fitness",
        f"{final_fitness:.2f}"
    )

    metric3.metric(
        "Fitness improvement",
        f"+{improvement:.2f}"
    )

    metric4.metric(
        "Average rating per slot",
        f"{average_rating:.3f}"
    )

    st.write("")

    # --------------------------------------------------
    # SCHEDULE TABLE
    # --------------------------------------------------

    st.subheader("Optimized TV schedule")
    st.caption(
        "The rating shows the value assigned to each programme "
        "in its selected time slot."
    )

    st.dataframe(
        schedule_df,
        width="stretch",
        hide_index=True,
        height=500,
        column_config={
            "Time Slot": st.column_config.TextColumn(
                "Time slot"
            ),
            "Program": st.column_config.TextColumn(
                "Programme"
            ),
            "Rating": st.column_config.NumberColumn(
                "Rating",
                format="%.2f"
            )
        }
    )

    st.download_button(
        "Download schedule as CSV",
        data=schedule_df.to_csv(index=False).encode("utf-8"),
        file_name="generated_tv_schedule.csv",
        mime="text/csv"
    )

    st.write("")

    # --------------------------------------------------
    # FITNESS CHART
    # --------------------------------------------------

    st.subheader("Fitness progress")
    st.caption(
        "Best fitness recorded from the initial population "
        "through generation 100."
    )

    fitness_df = pd.DataFrame({
        "Generation": range(len(fitness_history)),
        "Best Fitness": fitness_history
    })

    min_fitness = max(0, min(fitness_history) - 0.5)
    max_fitness = max(fitness_history) + 0.5
    last_generation = len(fitness_history) - 1

    fitness_chart = (
        alt.Chart(fitness_df)
        .mark_line(
            color="#4A9EEB",
            strokeWidth=3,
            point=alt.OverlayMarkDef(
                filled=True,
                size=25
            )
        )
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
                title="Best fitness score",
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
                    title="Best fitness",
                    format=".2f"
                )
            ]
        )
        .properties(height=320)
    )

    st.altair_chart(fitness_chart, width="stretch")

    # --------------------------------------------------
    # SCHEDULE VALIDATION
    # --------------------------------------------------

    st.subheader("Schedule validation")

    total_slots = len(schedule)
    unique_programs = len(set(schedule))
    expected_programs = set(result["programs"])

    valid_schedule = (
        total_slots == 18
        and set(schedule) == expected_programs
        and len(expected_programs) == 10
    )

    validation_col1, validation_col2 = st.columns(2)

    validation_col1.metric(
        "Time slots",
        f"{total_slots} / 18"
    )

    validation_col2.metric(
        "Unique programmes",
        f"{unique_programs} / 10"
    )

    st.write("")

    if valid_schedule:
        st.success(
            "Validation passed: the schedule has 18 time slots "
            "and includes all 10 programmes."
        )
    else:
        st.error(
            "Validation failed: check the number of time slots "
            "and whether all programmes are included."
        )
```
