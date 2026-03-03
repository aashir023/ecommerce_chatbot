import { ServiceCenter } from "./types";

interface ServiceCenterListProps {
  centers: ServiceCenter[];
}

const ServiceCenterList = ({ centers }: ServiceCenterListProps) => {
  return (
    <div className="space-y-2 animate-[chat-message-in_0.3s_ease-out] max-w-[90%]">
      <div className="flex items-end gap-2">
        <div className="w-7 h-7 rounded-full bg-chat-header flex items-center justify-center text-chat-header-foreground text-xs font-bold shrink-0">
          JE
        </div>
        <p className="text-sm text-chat-bubble-bot-foreground bg-chat-bubble-bot rounded-2xl rounded-bl-md px-4 py-2.5 shadow-sm">
          📍 Here are our <strong>9 service centers</strong> near you:
        </p>
      </div>
      <div className="ml-9 space-y-2 max-h-[300px] overflow-y-auto pr-1">
        {centers.map((center) => (
          <div
            key={center.id}
            className="bg-chat-bubble-bot rounded-xl p-3 shadow-sm border border-border/30"
          >
            <p className="text-sm font-semibold text-chat-bubble-bot-foreground">{center.name}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{center.address}</p>
            <div className="flex items-center justify-between mt-2">
              <a
                href={`tel:${center.phone}`}
                className="text-xs font-medium text-primary hover:underline"
              >
                📞 {center.phone}
              </a>
              {center.distance && (
                <span className="text-xs text-muted-foreground">{center.distance}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceCenterList;
