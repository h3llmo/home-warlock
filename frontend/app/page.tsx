import RealtimeCost from "@/components/RealtimeCost";
import BMWStatus from "@/components/BMWStatus";
import LiveConsumption from "@/components/LiveConsumption";
import MonthProjection from "@/components/MonthProjection";

export default function HomePage() {
  return (
    <>
      <RealtimeCost />
      <BMWStatus />
      <LiveConsumption />
      <MonthProjection />
    </>
  );
}
