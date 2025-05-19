CXX = g++
CXXFLAGS = -std=c++11 -Wall -g

SRCS = main.cpp utils.cpp graph.cpp shelter_manager.cpp
OBJS = $(SRCS:.cpp=.o)
TARGET = disaster_management

$(TARGET): $(OBJS)
	$(CXX) $(OBJS) -o $(TARGET)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: clean 