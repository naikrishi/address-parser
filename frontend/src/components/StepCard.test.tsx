import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { StepCard } from "./StepCard";
import type { PipelineStep } from "../types";

function makeStep(status: PipelineStep["status"]): PipelineStep {
	return {
		id: 2,
		title: "LLM Extraction",
		status,
		summary: "Fills missing fields from language model output.",
		details: {
			city: "Plano",
			postal_code: "75075",
		},
	};
}

describe("StepCard", () => {
	it("renders status labels", () => {
		render(<StepCard step={makeStep("complete")} />);
		expect(screen.getByText("Complete")).toBeInTheDocument();
	});

	it("renders details grid entries", () => {
		render(<StepCard step={makeStep("in_progress")} />);
		expect(screen.getByText("city")).toBeInTheDocument();
		expect(screen.getByText("Plano")).toBeInTheDocument();
		expect(screen.getByText("postal_code")).toBeInTheDocument();
		expect(screen.getByText("75075")).toBeInTheDocument();
	});

	it("hides details grid when details are missing", () => {
		render(
			<StepCard
				step={{
					id: 4,
					title: "Geocode",
					status: "pending",
					summary: "Waiting for geocode provider.",
				}}
			/>,
		);
		expect(screen.queryByText("city")).not.toBeInTheDocument();
	});
});
