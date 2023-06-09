import numpy as np  # numpy is faster in math operations

from edge import Edge
from face import Face
from point import Point


class BallPivotingAlgorithm:
    """
    An algorithm for reconstructing surfaces of a mesh.

    The algorithm works by checking a radius around a point to find another point and link them to create an edge.
    The algorithm then finds a third point from that edge in a certain radius to create a face.
    The algorithm then continues to use a new edge formed from a face to find a third point and create a new face.

    Works from a seed triangle and continues to create faces and edges until there are no more points left.

    To run -> initialise the class with a point cloud and radius, then call run() to run the algorithm. Other options are available to modify the user experience.
    """

    faces = []
    edges = []

    def __init__(self, radius: float, point_cloud: np.ndarray = None, file_location: str = None, iterations: int = None) -> None:
        """
        Initializes the Ball Pivoting Algorithm with the given point cloud and radius.
        :param point_cloud: The point cloud to be interpolated.
        :param radius: The radius of the ball used for pivoting.
        """
        self.point_cloud = point_cloud or np.ndarray([])
        if file_location:
            self.open_point_cloud(file_location)
            self.file_location = file_location
        self.radius = radius
        if iterations:
            self.iterations=iterations
        else:
            self.iterations = len(self.point_cloud)
        return

    def open_point_cloud(self, file_location: str) -> None:
        """
        Opens an object file, filtering out the points in the point cloud
        :param file_location: The location of the object file
        """

        file_list = ['obj']
        if file_location.split('.')[-1] not in file_list:
            raise ValueError(f"Only able to read object data of types {file_list}")

        with open(file_location, 'r') as f:
            # Initialise points to be added to numpy array
            points = []

            for line in f.readlines():
                # There must be text in the line and it must be a vertex
                if not len(line) > 3:
                    continue
                # Segments of string
                segments = line.split()

                if segments[0] != 'v': continue

                points.append([
                        float(segments[1]),
                        float(segments[2]),
                        float(segments[3])
                    ])

            self.point_cloud = np.array([Point(point) for point in points])

        return

    def find_seed_triangle(self) -> Face:
        """
        Finds a seed triangle to start the algorithm.
        :return: A seed triangle.
        """

        first_point = self.point_cloud[0]

        # Find second point by distance
        neighbours, distances = first_point.find_neighbouring_vertices_with_distance(self.point_cloud, self.radius)
        second_point = first_point.get_closest_point(neighbours, distances)

        first_edge = Edge(first_point, second_point)
        self.edges.append(first_edge)

        # Find third point through shared neighbour along edge (Cylindrical space)
        third_point = first_edge.find_third_point(self.point_cloud, self.radius, self.faces)
        
        second_edge = Edge(second_point, third_point)
        
        third_edge = Edge(third_point, first_point)

        self.edges.append(second_edge)
        self.edges.append(third_edge)

        # np.where(xxx)[0][0] gets the index of the point in the point cloud for use in saving to file later
        seed_triangle = Face((first_point, second_point, third_point), (first_edge, second_edge, third_edge), (np.where(self.point_cloud == first_point)[0][0], np.where(self.point_cloud == second_point)[0][0], np.where(self.point_cloud == third_point)[0][0]))

        return seed_triangle

    def pivot_ball(self, edge:Edge):
        """
        Pivots the ball around the given edge until it touches another point.
        :param edge: The edge to pivot the ball around.
        :return: The next triangle formed by the ball pivoting around the edge.
        """
        
        # Find third point of triangle
        third_point = edge.find_third_point(self.point_cloud, self.radius, self.faces)

        second_edge = Edge(edge.p1, third_point)
        third_edge = Edge(edge.p2, third_point)
        self.edges.append(second_edge)
        self.edges.append(third_edge)

        self.edges = list(set(self.edges))
        
        (np.where(self.point_cloud == edge.p1)[0][0], np.where(self.point_cloud == edge.p2)[0][0], np.where(self.point_cloud == third_point)[0][0])
        # np.where(xxx)[0][0] gets the index of the point in the point cloud for use in saving to file later
        return Face((edge.p1, edge.p2, third_point), (edge, second_edge, third_edge), (np.where(self.point_cloud == edge.p1)[0][0], np.where(self.point_cloud == edge.p2)[0][0], np.where(self.point_cloud == third_point)[0][0]))

    def write_to_file(self, file_location:str=None) -> None:
        """
        Writes the triangle mesh to an object file.
        :param file_location: The location of the object file.
        """

        if file_location is None:
            file_location = self.file_location
        edited_file_location = file_location.split('.')
        edited_file_location[-2] += '_edited'

        with open(".".join(edited_file_location), 'w') as f:
            f.write(f"# {file_location}\n")

            for point in self.point_cloud:
                f.write(f"v {point.x} {point.y} {point.z}\n")
            
            f.write(f"\n")

            for face in self.faces:
                f.write(f"f {face.p1_index+1} {face.p2_index+1} {face.p3_index+1}\n")
        
        # Create point cloud file
        if file_location is None:
            file_location = self.file_location
        edited_file_location = file_location.split('.')
        edited_file_location[-2] += '_point_cloud'
        with open(".".join(edited_file_location), 'w') as f:
            f.write(f"# {file_location}\n")

            for point in self.point_cloud:
                f.write(f"v {point.x} {point.y} {point.z}\n")

        return
    
    def points_left(self) -> bool:
        """
        Checks if there are any edges that don't have 2 connections.
        :return: True if there are points left, False otherwise.
        """

        # ! Not implemented yet. Don't worry about this
        
        for edge in self.edges:
            if edge.connections < 2:
                return True
            
        return False


    def run(self):
        """
        Runs the Ball Pivoting Algorithm to compute a triangle mesh interpolating the point cloud.
        :return: A triangle mesh interpolating the point cloud.
        """
        seed_triangle = self.find_seed_triangle()
        self.faces.append(seed_triangle)
        edge = seed_triangle.get_new_edge()
        for i in range(self.iterations): # Only run x iterations if you only want x faces (If it's a large point cloud, creating the entire mesh will take a while)
            
            face = self.pivot_ball(edge)
            self.faces.append(face)
            
            edge = face.get_new_edge() # Get the next edge to pivot around from the new face
            print(f"Point: {i+1}/{self.iterations} ☑️")
            k = 0
            # If you can't find the next edge, check on all other faces to see if there is one available, if not, quit as there are no more faces to add
            while edge == None:
                if k > len(self.faces): self.write_to_file(); quit()
                face = self.faces[k]
                edge = face.get_new_edge()
                k += 1

        self.write_to_file()

        return np.array([])

def main(radius:float, file_location:str, iterations:int):

    bpa = BallPivotingAlgorithm(radius=radius, file_location=file_location, iterations=iterations)
    bpa.run()


if __name__ == '__main__':

    main(radius=0.003, file_location='stanford-bunny.obj', iterations=50)
